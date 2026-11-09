
from pathlib import Path
import os
import pandas as pd
import streamlit as st
from dotenv import dotenv_values

from extractor import prepare_document, extract
from document_classifier import classify
from comparison import compare_all, validate_rows

from explainer import (
    AIError,
    definitions,
    doctor_questions,
    export_files,
    pdf_report,
    result_explanation,
    reference_label,
    DISCLAIMER
)

ROOT = Path(__file__).parent

st.set_page_config(
    page_title='MediSure AI',
    page_icon='🧪',
    layout='wide'
)

st.markdown(
    '<style>' + (ROOT / 'styles.css').read_text() + '</style>',
    unsafe_allow_html=True
)

S = st.session_state

if 'stage' not in S:
    S.stage = 'upload'

if 'generation' not in S:
    S.generation = 0

local = dotenv_values(ROOT / '.env')


def config(name, default=''):
    value = os.getenv(name) or local.get(name)

    if value:
        return str(value).strip()

    try:
        return str(st.secrets.get(name, default)).strip()
    except FileNotFoundError:
        return default


def goto(stage):
    S.stage = stage
    st.rerun()


def clear_report():
    for k in ['rows', 'results', 'meanings', 'ai_error', 'notice']:
        S.pop(k, None)

    S.generation += 1
    goto('upload')


# ==========================================
# APP HEADER
# ==========================================

st.markdown(
    '<div class="ms-kicker">YOUR LAB RESULTS, MADE CLEARER</div>',
    unsafe_allow_html=True
)

st.title('MediSure AI')

st.markdown(
    '<p class="ms-intro">Understand your laboratory results in three guided steps — with your review at the centre.</p>',
    unsafe_allow_html=True
)

step_labels = [
    ('upload', 'Upload'),
    ('verify', 'Verify'),
    ('results', 'Understand')
]

step_idx = {
    'upload': 0,
    'verify': 1,
    'results': 2
}.get(S.stage, 0)

steps = ''.join(
    f'<div class="ms-step {"active" if i == step_idx else "done" if i < step_idx else ""}">'
    f'<b>{"✓" if i < step_idx else i + 1}</b>'
    f'<span>{label}</span></div>'
    for i, (_, label) in enumerate(step_labels)
)

st.markdown(
    '<div class="ms-progress">' + steps + '</div>',
    unsafe_allow_html=True
)

# Configured by the team; visitors never enter keys or select models.
key = config('GEMINI_API_KEY')
model = config('GEMINI_MODEL')


# ==========================================
# STEP 1: UPLOAD
# ==========================================

if S.stage == 'upload':

    st.markdown(
        '<div class="ms-eyebrow">STEP 01 / 03</div>',
        unsafe_allow_html=True
    )

    st.header('Upload your report')

    st.write(
        'Upload a PDF or image of a lab report. '
        'Review and confirm its values before we compare them.'
    )

    st.markdown(
        '<div class="ms-note">Your document is processed only after you agree. '
        'Use a fictional or de-identified report for demonstrations.</div>',
        unsafe_allow_html=True
    )

    upload = st.file_uploader(
        'Choose a lab report',
        type=['pdf', 'png', 'jpg', 'jpeg'],
        key=f'upload_{S.generation}'
    )

    st.caption(
        'Up to 10 MB and 8 PDF pages. Use one patient’s report at a time.'
    )

    consent = st.checkbox(
        'I agree to send this report to Google Gemini for processing.'
    )

    st.caption(
        'This app has no report database. Reports are held temporarily '
        'in the session. Google’s processing policies apply. '
        'Use fictional or de-identified reports for the demo.'
    )

    if st.button('Read report', type='primary'):

        if not key or not model:
            st.error(
                'Report processing is not configured yet. '
                'Please contact the project team.'
            )

        elif upload is None:
            st.warning('Choose a file first.')

        elif not consent:
            st.warning('Tick the processing acknowledgement first.')

        else:
            try:
                with st.status(
                    'Reading report…',
                    expanded=True
                ) as status:

                    parts, routes = prepare_document(
                        upload.getvalue(),
                        upload.name
                    )

                    st.write('File opened successfully.')

                    check = classify(key, model, parts)

                    if check['classification'] != 'lab_report':

                        status.update(
                            label='Document check stopped',
                            state='error'
                        )

                        st.warning(
                            (
                                'This does not appear to be a lab report. '
                                if check['classification'] == 'not_lab_report'
                                else 'The document is unclear. '
                            )
                            + str(check.get('reason', ''))
                        )

                    else:
                        st.write(
                            'Document check passed. Extracting test rows…'
                        )

                        rows = extract(key, model, parts)

                        S.rows = rows
                        S.pop('results', None)
                        S.pop('meanings', None)

                        status.update(
                            label='Ready to verify',
                            state='complete'
                        )

                        goto('verify')

            except (ValueError, AIError) as exc:
                st.error(str(exc))


# ==========================================
# STEP 2: VERIFICATION
# ==========================================

elif S.stage == 'verify':

    st.markdown(
        '<div class="ms-eyebrow">STEP 02 / 03</div>',
        unsafe_allow_html=True
    )

    st.header('Verify every value')

    st.info(
        'Compare every row with your original report. '
        'Correct errors and add any omitted tests. '
        'Never invent a missing range.'
    )

    st.caption(
        'Numeric results only. Missing or nonnumeric results block '
        'confirmation. Missing or unsuitable ranges and units are '
        'marked Unavailable.'
    )

    with st.form('verification'):

        edited = st.data_editor(
            pd.DataFrame(S.rows),
            num_rows='dynamic',
            hide_index=True,
            width='stretch',
            column_order=[
                'category',
                'test_name',
                'value',
                'unit',
                'reference_range',
                'range_unit',
                'note'
            ],
            column_config={
                k: st.column_config.TextColumn(label)
                for k, label in [
                    ('category', 'Category'),
                    ('test_name', 'Test name'),
                    ('value', 'Value'),
                    ('unit', 'Unit'),
                    ('reference_range', 'Report range'),
                    ('range_unit', 'Range unit'),
                    ('note', 'Extraction note')
                ]
            },
            key=f'editor_{S.generation}'
        )

        confirm = st.checkbox(
            'I checked all tests, values, units and applicable '
            'ranges against the original report.'
        )

        submitted = st.form_submit_button(
            'Confirm and compare',
            type='primary'
        )

    if submitted:

        rows = edited.fillna('').astype(str).to_dict('records')

        for r in rows:
            r['category'] = (
                r.get('category', '').strip()
                or 'Other tests'
            )

        errors = validate_rows(rows)

        if not confirm:
            errors.append(
                'Tick the verification checkbox to continue.'
            )

        if errors:
            for error in errors:
                st.error(error)

        else:
            S.rows = rows
            S.results = compare_all(rows)
            S.meanings = {}
            S.ai_error = ''

            try:
                with st.spinner(
                    'Generating explanations for your laboratory tests…'
                ):
                    S.meanings = definitions(
                        key,
                        model,
                        S.results
                    )

            except AIError as exc:
                S.ai_error = str(exc)

            goto('results')

    if st.button('Upload a different report'):
        clear_report()


# ==========================================
# STEP 3: RESULTS
# ==========================================

elif S.stage == 'results':

    st.markdown(
        '<div class="ms-eyebrow">STEP 03 / 03</div>',
        unsafe_allow_html=True
    )

    st.header('Your report, explained')

    rows = S.results
    meanings = S.get('meanings', {})

    normal = sum(
        r['status'] == 'Normal'
        for r in rows
    )

    outside = sum(
        r['status'] in ('Low', 'High')
        for r in rows
    )

    unavailable = len(rows) - normal - outside

    cols = st.columns(3)

    for c, label, n in zip(
        cols,
        ['Within range', 'Outside range', 'Unavailable'],
        [normal, outside, unavailable]
    ):
        c.metric(label, n)

    st.caption(
        'Within range means only within the ranges supplied '
        'in this report; it does not rule out illness.'
    )

    # ======================================
    # UNUSUAL RESULT VERIFICATION WARNINGS
    # ======================================

    review_rows = [
        r for r in rows
        if r.get('review_flag')
    ]

    if review_rows:

        st.warning(
            f'{len(review_rows)} result(s) are unusually far from their '
            'report-printed ranges and need verification. '
            'This is a screening flag, NOT a medical critical-value assessment. '
            'Check the original report, value and units. '
            'If confirmed, contact a qualified clinician promptly.'
        )

        for r in review_rows:
            st.write(
                f"**Verify {r['test_name']}:** "
                f"{r['value']} {r['unit']} "
                f"(report range: {reference_label(r)}). "
                f"{r.get('review_reason', '')}"
            )

    # ======================================
    # AI EXPLANATIONS
    # ======================================

    if S.get('ai_error'):

        st.warning(
            'AI explanations are unavailable. '
            'Python comparisons are still shown.'
        )

        st.error(S.ai_error)

        if st.button('Retry explanations'):

            try:
                with st.spinner('Retrying…'):
                    S.meanings = definitions(
                        key,
                        model,
                        rows
                    )

                S.ai_error = ''
                st.rerun()

            except AIError as exc:
                st.error(str(exc))

    # ======================================
    # RESULTS GROUPED BY CATEGORY
    # ======================================

    for category in dict.fromkeys(
        r['category'] for r in rows
    ):

        st.subheader(category)
        table = []

        for i, r in enumerate(rows):

            if r['category'] == category:

                table.append({
                    'Test': r['test_name'],
                    'Value': r['value'] + ' ' + r['unit'],
                    'Report range': reference_label(r),
                    'Status': r['status'],
                    'Explanation': result_explanation(
                        r,
                        meanings.get(i, '')
                    )
                })

        st.dataframe(
            pd.DataFrame(table),
            hide_index=True,
            width='stretch'
        )

    # ======================================
    # DOCTOR QUESTIONS
    # ======================================

    st.subheader('Questions for your doctor')

    for q in doctor_questions(rows):
        st.write('• ' + q)

    st.info(DISCLAIMER)

    # ======================================
    # DOWNLOAD RESULTS
    # ======================================

    st.subheader('Take your results with you')

    st.caption(
        'Download a polished PDF summary for easy reading '
        'or a CSV for your records.'
    )

    html, csv = export_files(rows, meanings)

    a, b = st.columns(2)

    a.download_button(
        'Download PDF',
        pdf_report(rows, meanings),
        'MediSure_AI_report.pdf',
        'application/pdf',
        type='primary',
        width='stretch'
    )

    b.download_button(
        'Download CSV',
        csv,
        'MediSure_AI_values.csv',
        'text/csv',
        width='stretch'
    )

    c, d = st.columns(2)

    with c:
        if st.button(
            'Edit verified values',
            width='stretch'
        ):
            S.pop('results', None)
            S.pop('meanings', None)
            S.generation += 1
            goto('verify')

    with d:
        if st.button(
            'Clear report and start again',
            width='stretch'
        ):
            clear_report()


# ==========================================
# FOOTER
# ==========================================

st.markdown(
    '<div class="ms-footer">MediSure AI · Educational prototype only. '
    'No diagnosis or treatment advice. '
    'Discuss your results with a qualified healthcare professional.</div>',
    unsafe_allow_html=True
)

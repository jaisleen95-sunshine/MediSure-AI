
"""Deterministic report-range comparison and non-clinical plausibility checks.

No diagnostic or critical-value thresholds are supplied by this module.
A recheck flag means that a value is VERY far from the user's verified,
report-printed reference range; it is not a medical urgency classification.
"""

import re
from decimal import Decimal, InvalidOperation

NUM = r'[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:[eE][+-]?\d+)?|[+-]?\.\d+(?:[eE][+-]?\d+)?'
NUMBER = re.compile(rf'(?:{NUM})\Z')

# Demonstration heuristic, NOT a clinical cutoff.
RECHECK_FACTOR = Decimal('5')


def number(value):
    s = str(value).strip()
    if not NUMBER.fullmatch(s):
        raise ValueError(
            'Enter a number; use a dot for decimals and commas only for thousands.'
        )
    try:
        n = Decimal(s.replace(',', ''))
    except InvalidOperation:
        raise ValueError('Enter a valid number.') from None
    if not n.is_finite() or abs(n) > Decimal('1e15'):
        raise ValueError('Number is outside this prototype’s supported limits.')
    return n


def unit_key(s):
    # No automatic unit conversion.
    return str(s).strip().replace('μ', 'µ').replace(' ', '').casefold()


def parse_range(text, range_unit=''):
    """Parse only unambiguous ranges explicitly supplied in the report."""
    s = str(text).strip().replace('–', '-').replace('—', '-').replace('−', '-')
    s = s.replace('≤', '<=').replace('≥', '>=').replace('＜', '<').replace('＞', '>')
    s = re.sub(r'\s+', ' ', s).strip()

    if range_unit:
        unit = str(range_unit).strip()
        if s.casefold().endswith(unit.casefold()):
            before = s[:-len(unit)].rstrip()
            if before and (before[-1].isdigit() or before[-1] in '.,'):
                s = before

    m = re.fullmatch(rf'(<=|>=|<|>)\s*({NUM})', s)
    if m:
        return m[1], number(m[2])

    phrases = [
        (r'(?:below|less than|under|lower than)', '<'),
        (r'(?:at most|no more than|not above|up to)', '<='),
        (r'(?:above|greater than|more than|over|higher than)', '>'),
        (r'(?:at least|no less than|not below|minimum of)', '>='),
    ]

    for phrase, op in phrases:
        m = re.fullmatch(rf'{phrase}\s*({NUM})', s, flags=re.I)
        if m:
            return op, number(m[1])

    m = re.fullmatch(rf'({NUM})\s*(?:-|to)\s*({NUM})', s, flags=re.I)
    if m:
        low, high = number(m[1]), number(m[2])
        if low >= high:
            raise ValueError(
                'Range lower limit must be smaller than its upper limit.'
            )
        return 'interval', low, high

    raise ValueError(
        'Use a clear report range such as 12-15, Below 200, '
        'At least 40, <200 or >=40.'
    )


def validate_rows(rows):
    errors = []

    if not rows:
        return ['No test rows were found. Upload a clearer report.']

    for i, row in enumerate(rows):
        label = row.get('test_name', '').strip() or f'Row {i + 1}'

        if not row.get('test_name', '').strip():
            errors.append(f'{label}: test name is missing.')

        value = row.get('value', '').strip()

        if not value:
            errors.append(f'{label}: value is missing.')
        else:
            try:
                number(value)
            except ValueError as exc:
                errors.append(f'{label}: {exc}')

    return errors


def check_unusual(value, bounds, status):
    """
    Flag very large deviations for manual rechecking.

    This is a numerical screening rule, not clinical risk scoring.
    It only works with positive relevant reference bounds.
    """

    if status not in ('Low', 'High'):
        return ''

    op, a = bounds[:2]
    lower = upper = None

    if op == 'interval':
        lower, upper = a, bounds[2]
    elif op in ('<', '<='):
        upper = a
    elif op in ('>', '>='):
        lower = a

    if status == 'High' and upper is not None and upper > 0:
        if value > RECHECK_FACTOR * upper:
            return (
                'Value is more than five times the report’s upper reference bound. '
                'Recheck transcription, units and the original laboratory report.'
            )

    if status == 'Low' and lower is not None and lower > 0:
        if value < lower / RECHECK_FACTOR:
            return (
                'Value is below one-fifth of the report’s lower reference bound. '
                'Recheck transcription, units and the original laboratory report.'
            )

    return ''


def compare(row):
    result = dict(row)

    result.update(
        status='Unavailable',
        reason='',
        review_flag=False,
        review_reason=''
    )

    try:
        value = number(row['value'])

        if not row.get('unit', '').strip() or not row.get('range_unit', '').strip():
            raise ValueError(
                'Result or reference-range unit is missing; comparison unavailable.'
            )

        if unit_key(row['unit']) != unit_key(row['range_unit']):
            raise ValueError(
                'Result and range units differ. No automatic conversion is performed.'
            )

        if not row.get('reference_range', '').strip():
            raise ValueError('No reference range is printed or confirmed.')

        bounds = parse_range(
            row['reference_range'],
            row['range_unit']
        )

        op, a = bounds[:2]

        if op == 'interval':
            status = (
                'Low' if value < a
                else 'High' if value > bounds[2]
                else 'Normal'
            )
        elif op == '<':
            status = 'Normal' if value < a else 'High'
        elif op == '<=':
            status = 'Normal' if value <= a else 'High'
        elif op == '>':
            status = 'Normal' if value > a else 'Low'
        else:
            status = 'Normal' if value >= a else 'Low'

        result['status'] = status

        result['review_reason'] = check_unusual(
            value, bounds, status
        )

        result['review_flag'] = bool(result['review_reason'])

    except ValueError as exc:
        result['reason'] = str(exc)

    return result


def compare_all(rows):
    errors = validate_rows(rows)

    if errors:
        raise ValueError('\n'.join(errors))

    return [compare(row) for row in rows]


def status_sentence(row):
    return {
        'Low': 'Below, or at an excluded boundary of, the reference range printed in your report.',
        'High': 'Above, or at an excluded boundary of, the reference range printed in your report.',
        'Normal': 'Within the reference range printed in your report.',
        'Unavailable': 'Comparison unavailable. ' + row.get('reason', ''),
    }[row['status']]


# Fictional demo fixtures only.
# Never used as fallback for uploaded reports.

DATA = [
    ('Complete Blood Count (CBC)', 'Hemoglobin', '11.2', 'g/dL', '12.0 - 15.5'),
    ('Complete Blood Count (CBC)', 'White Blood Cells (WBC)', '7,200', '/µL', '4,000 - 11,000'),
    ('Complete Blood Count (CBC)', 'Platelet Count', '265', '×10³/µL', '150 - 450'),
    ('Lipid Profile', 'Total Cholesterol', '214', 'mg/dL', '<200'),
    ('Lipid Profile', 'LDL Cholesterol', '128', 'mg/dL', '<100'),
    ('Lipid Profile', 'HDL Cholesterol', '52', 'mg/dL', '>50'),
    ('Lipid Profile', 'Triglycerides', '140', 'mg/dL', '<150'),
]

MEANINGS = [
    'Hemoglobin is a protein in red blood cells that carries oxygen.',
    'White blood cells are part of the body’s defense against infection.',
    'Platelets are cell fragments that help blood clot.',
    'This measures the total amount of cholesterol in your blood.',
    'This measures cholesterol carried by low-density lipoproteins.',
    'This measures cholesterol carried by high-density lipoproteins.',
    'Triglycerides are a type of fat found in your blood.',
]


def demo_rows():
    return [
        dict(
            category=c,
            test_name=t,
            value=v,
            unit=u,
            reference_range=r,
            range_unit=u,
            note='Fictional demo data'
        )
        for c, t, v, u, r in DATA
    ]


def demo_meanings(rows):
    lookup = {r[1]: m for r, m in zip(DATA, MEANINGS)}

    return {
        i: lookup.get(
            r['test_name'],
            'Ask your laboratory what this test measures.'
        )
        for i, r in enumerate(rows)
    }

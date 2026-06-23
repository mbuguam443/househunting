from datetime import date, timedelta
from calendar import monthrange
from .models import Tenancy, RentPayment


def _next_month(y, m):
    if m == 12:
        return y + 1, 1
    return y, m + 1


def _iter_months(start, end):
    y, m = start.year, start.month
    ey, em = end.year, end.month
    while (y < ey) or (y == ey and m <= em):
        yield y, m
        y, m = _next_month(y, m)


def generate_rent_payments(landlord=None):
    created = 0
    today = date.today()
    tenancies = Tenancy.objects.filter(status='active')
    if landlord:
        tenancies = tenancies.filter(unit__property__owner=landlord)

    for tenancy in tenancies:
        loop_start = max(tenancy.start_date, today - timedelta(days=365))
        loop_end = today + timedelta(days=30)

        for y, m in _iter_months(loop_start, loop_end):
            _, last_day = monthrange(y, m)
            due = date(y, m, min(tenancy.start_date.day, last_day))

            if RentPayment.objects.filter(tenancy=tenancy, due_date=due).exists():
                continue

            status = 'overdue' if due < today else 'pending'
            RentPayment.objects.create(
                tenancy=tenancy, amount=tenancy.monthly_rent,
                due_date=due, status=status,
            )
            created += 1

    return created


def mark_overdue_payments(landlord=None):
    qs = RentPayment.objects.filter(status='pending', due_date__lt=date.today())
    if landlord:
        qs = qs.filter(tenancy__unit__property__owner=landlord)
    return qs.update(status='overdue')

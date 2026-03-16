"""Social charge allocation to PCG accounts."""
import structlog
from decimal import Decimal

logger = structlog.get_logger()

# Standard PCG payroll accounts
PAYROLL_ACCOUNTS = {
    "641100": "Salaires et appointements",
    "645100": "Cotisations URSSAF",
    "645300": "Cotisations caisses de retraite",
    "645400": "Cotisations mutuelles",
    "421000": "Personnel - Remunerations dues",
    "431000": "Securite sociale",
    "437000": "Autres organismes sociaux",
}


def allocate_charges(payslip_data: dict) -> list[dict]:
    """Generate journal entry lines from payslip data.

    Standard payroll entry:
    Debit 641100 (Salaires) = Gross
    Debit 645100 (URSSAF employer) = employer URSSAF
    Debit 645300 (Retraite employer) = employer retirement
    Credit 421000 (Personnel) = Net salary
    Credit 431000 (Securite sociale) = total URSSAF (employee + employer)
    Credit 437000 (Autres organismes) = retirement + other
    """
    gross = Decimal(str(payslip_data.get("gross_salary", 0)))
    net = Decimal(str(payslip_data.get("net_salary", 0)))
    urssaf = Decimal(str(payslip_data.get("urssaf", 0)))
    retirement = Decimal(str(payslip_data.get("retirement", 0)))
    employer_charges = Decimal(str(payslip_data.get("employer_charges", 0)))

    # Split employer charges
    employer_urssaf = (employer_charges * Decimal("0.6")).quantize(Decimal("0.01"))
    employer_retirement = employer_charges - employer_urssaf  # remainder to avoid rounding gaps

    # Employee charges not covered by explicit urssaf/retirement (CSG/CRDS, etc.)
    employee_other = gross - net - urssaf - retirement

    # Credit side for social organisms: employee portion + employer portion
    credit_431 = urssaf + employer_urssaf + (employee_other if employee_other > 0 else Decimal("0"))
    credit_437 = retirement + employer_retirement

    lines = [
        {"account_code": "641100", "account_name": "Salaires", "debit": gross, "credit": Decimal("0")},
        {"account_code": "645100", "account_name": "Cotisations URSSAF", "debit": employer_urssaf, "credit": Decimal("0")},
        {"account_code": "645300", "account_name": "Cotisations retraite", "debit": employer_retirement, "credit": Decimal("0")},
        {"account_code": "421000", "account_name": "Personnel", "debit": Decimal("0"), "credit": net},
        {"account_code": "431000", "account_name": "Securite sociale", "debit": Decimal("0"), "credit": credit_431},
        {"account_code": "437000", "account_name": "Autres organismes", "debit": Decimal("0"), "credit": credit_437},
    ]

    logger.info("payroll_charges_allocated", gross=str(gross), net=str(net))
    return lines

def calculate_case(
    area,
    yield_per_acre,
    loss_pct,
    price_qtl,
    cost_items_per_acre,
    loan,
    annual_rate_pct,
    months,
    depreciation,
):
    area = float(area)
    yield_per_acre = float(yield_per_acre)
    loss_pct = float(loss_pct)
    price_qtl = float(price_qtl)
    loan = float(loan)
    annual_rate_pct = float(annual_rate_pct)
    months = float(months)
    depreciation = float(depreciation)

    gross_kg = area * yield_per_acre
    saleable_kg = gross_kg * max(0.0, 1 - loss_pct / 100)
    saleable_qtl = saleable_kg / 100

    cash_cost_per_acre = sum(float(v) for v in cost_items_per_acre.values())
    cash_cost = area * cash_cost_per_acre

    effective_interest_rate = annual_rate_pct / 100 * months / 12
    interest = loan * effective_interest_rate
    repayment_obligation = loan + interest

    revenue = saleable_qtl * price_qtl
    total_accounting_cost = cash_cost + interest + depreciation
    cash_profit = revenue - cash_cost - interest
    accounting_profit = revenue - total_accounting_cost
    margin = accounting_profit / revenue * 100 if revenue else 0

    break_even_price = total_accounting_cost / saleable_qtl if saleable_qtl else 0
    price_cushion = (
        (price_qtl - break_even_price) / price_qtl * 100 if price_qtl else 0
    )

    break_even_saleable_kg = (
        total_accounting_cost / (price_qtl / 100) if price_qtl else 0
    )
    saleable_factor = max(1e-9, 1 - loss_pct / 100)
    break_even_gross_kg = break_even_saleable_kg / saleable_factor
    break_even_yield = break_even_gross_kg / area if area else 0
    yield_cushion = (
        (yield_per_acre - break_even_yield) / yield_per_acre * 100
        if yield_per_acre
        else 0
    )

    harvest_coverage = (
        revenue / repayment_obligation if repayment_obligation else 0
    )

    own_contribution = max(cash_cost - loan, 0)
    excess_financing = max(loan - cash_cost, 0)

    target_coverage = 1.25
    supportable_by_revenue = (
        revenue / (target_coverage * (1 + effective_interest_rate))
        if (1 + effective_interest_rate) > 0
        else 0
    )
    indicative_max_supportable_loan = min(cash_cost, supportable_by_revenue)

    return {
        "gross_kg": gross_kg,
        "saleable_kg": saleable_kg,
        "saleable_qtl": saleable_qtl,
        "cash_cost_per_acre": cash_cost_per_acre,
        "cash_cost": cash_cost,
        "interest": interest,
        "repayment_obligation": repayment_obligation,
        "revenue": revenue,
        "total_accounting_cost": total_accounting_cost,
        "cash_profit": cash_profit,
        "accounting_profit": accounting_profit,
        "margin": margin,
        "break_even_price": break_even_price,
        "price_cushion": price_cushion,
        "break_even_yield": break_even_yield,
        "yield_cushion": yield_cushion,
        "harvest_coverage": harvest_coverage,
        "own_contribution": own_contribution,
        "excess_financing": excess_financing,
        "indicative_max_supportable_loan": indicative_max_supportable_loan,
    }


def run_scenarios(base_inputs):
    scenarios = [
        ("Strong market", 0.10, 0.10),
        ("Base case", 0.00, 0.00),
        ("Price stress", 0.00, -0.10),
        ("Yield stress", -0.10, 0.00),
        ("Moderate stress", -0.10, -0.10),
        ("Severe stress", -0.20, -0.20),
    ]

    rows = []
    for name, ychg, pchg in scenarios:
        r = calculate_case(
            area=base_inputs["area"],
            yield_per_acre=base_inputs["yield_per_acre"] * (1 + ychg),
            loss_pct=base_inputs["loss_pct"],
            price_qtl=base_inputs["price_qtl"] * (1 + pchg),
            cost_items_per_acre=base_inputs["cost_items_per_acre"],
            loan=base_inputs["loan"],
            annual_rate_pct=base_inputs["annual_rate_pct"],
            months=base_inputs["months"],
            depreciation=base_inputs["depreciation"],
        )
        rows.append(
            {
                "Scenario": name,
                "Yield change": ychg,
                "Price change": pchg,
                "Revenue": r["revenue"],
                "Accounting profit": r["accounting_profit"],
                "Margin": r["margin"],
                "Harvest coverage": r["harvest_coverage"],
            }
        )
    return rows


def resilience_label(base_result, scenario_rows):
    moderate = next(
        row for row in scenario_rows if row["Scenario"] == "Moderate stress"
    )

    if (
        base_result["accounting_profit"] > 0
        and base_result["harvest_coverage"] >= 1.25
        and base_result["price_cushion"] >= 20
        and moderate["Accounting profit"] >= 0
    ):
        return (
            "Strong",
            "The base case is profitable, repayment coverage is comparatively comfortable, "
            "and the model remains profitable under the moderate stress scenario.",
        )

    if (
        base_result["accounting_profit"] > 0
        and base_result["harvest_coverage"] >= 1.05
    ):
        return (
            "Moderate",
            "The base case remains positive, but one or more downside-resilience measures are thin.",
        )

    return (
        "Stressed",
        "The base case shows weak repayment coverage and/or negative modeled accounting profit.",
    )

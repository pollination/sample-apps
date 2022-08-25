"""Calculate PAR from irradiance."""


def calculate_par(irr: float):
    """
    Calculate PAR from irradiance based on https://ieeexplore.ieee.org/document/8521475

    Crops classifications based on Table 3 are <3.13 - 3.13~5.48 and >5.48 for low PAR,
    medium PAR and high PAR.

    args:
        irr: averaged irradiance value in kwh/m2
    """
    # NOTE: 1.5 is here to adjust the values for the cumulative sky - remove it after
    # validating the results
    daily_irr = 24 * irr / 1.5 # multiply by 24 to get the value for 24 hours
    par_full_spectrum = daily_irr * 3600 / 10 ** 6  # value in MJ/m2-day
    par_400_700 = par_full_spectrum * 43 / 100  # 43% of the spectrum
    return par_400_700


def calculate_ppfd(irr: float):
    par = calculate_par(irr)
    return par * 127.79


def calc_par_clf(irr_values):
    """Calculate PAR values and % classification."""
    par_values = [calculate_par(round(float(v))) for v in irr_values]
    total_count = len(par_values)
    count = [0, 0, 0]
    for v in par_values:
        if v <= 3.13:
            count[0] += 1
        elif v <= 5.48:
            count[1] += 1
        else:
            count[2] += 1

    # convert to %
    count = [round(c * 100 / total_count, 2) for c in count]

    return par_values, {'low': count[0], 'medium': count[1], 'high': count[2]}


def calc_ppfd_clf(irr_values):
    """Calculate PPFD values and % classification."""
    ppfd_values = [calculate_ppfd(round(float(v))) for v in irr_values]
    total_count = len(ppfd_values)
    count = [0, 0, 0]
    for v in ppfd_values:
        if v <= 300:
            count[0] += 1
        elif v <= 600:
            count[1] += 1
        else:
            count[2] += 1

    # convert to %
    count = [round(c * 100 / total_count, 2) for c in count]

    return ppfd_values, {'low': count[0], 'medium': count[1], 'high': count[2]}

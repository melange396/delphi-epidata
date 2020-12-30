from flask import Blueprint

from .._query import execute_query, filter_integers, filter_strings
from .._validate import extract_integer, extract_integers, extract_strings, require_all

bp = Blueprint("flusurv", __name__)


@bp.route("/", methods=("GET", "POST"))
def handle():
    require_all("epiweeks", "locations")

    epiweeks = extract_integers("epiweeks")
    locations = extract_strings("locations")
    issues = extract_integers("issues")
    lag = extract_integer("lag")

    # basic query info
    table = "`flusurv` fs"
    fields = "fs.`release_date`, fs.`issue`, fs.`epiweek`, fs.`location`, fs.`lag`, fs.`rate_age_0`, fs.`rate_age_1`, fs.`rate_age_2`, fs.`rate_age_3`, fs.`rate_age_4`, fs.`rate_overall`"
    order = "fs.`epiweek` ASC, fs.`location` ASC, fs.`issue` ASC"

    params = dict()
    # build the epiweek filter
    condition_epiweek = filter_integers("fs.`epiweek`", epiweeks, "epiweek", params)
    # build the location filter
    condition_location = filter_strings("fs.`location`", locations, "loc", params)
    if issues is not None:
        # build the issue filter
        condition_issue = filter_integers("fs.`issue`", issues, "issue", params)
        # final query using specific issues
        query = f"SELECT {fields} FROM {table} WHERE ({condition_epiweek}) AND ({condition_location}) AND ({condition_issue}) ORDER BY {order}"
    elif lag is not None:
        # build the lag filter
        condition_lag = "(fs.`lag` = :lag)"
        params["lag"] = lag
        # final query using lagged issues
        query = f"SELECT {fields} FROM {table} WHERE ({condition_epiweek}) AND ({condition_location}) AND ({condition_lag}) ORDER BY {order}"
    else:
        # final query using most recent issues
        subquery = f"(SELECT max(`issue`) `max_issue`, `epiweek`, `location` FROM {table} WHERE ({condition_epiweek}) AND ({condition_location}) GROUP BY `epiweek`, `location`) x"
        condition = "x.`max_issue` = fs.`issue` AND x.`epiweek` = fs.`epiweek` AND x.`location` = fs.`location`"
        query = f"SELECT {fields} FROM {table} JOIN {subquery} ON {condition} ORDER BY {order}"

    fields_string = ["release_date", "location"]
    fields_int = ["issue", "epiweek", "lag"]
    fields_float = [
        "rate_age_0",
        "rate_age_1",
        "rate_age_2",
        "rate_age_3",
        "rate_age_4",
        "rate_overall",
    ]

    # send query
    return execute_query(query, params, fields_string, fields_int, fields_float)

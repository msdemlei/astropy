"""
Tests for Markus' (somewhat informal) DM annotation proposal.

Well, actually: I can't be bothered to figure out pytest's setup here, so
for now this is just some sample code; I'll convert it do something 
palatable to pytest when this is going somewhere.

vodml-timeseries is taken out of a production service:

http://dc.g-vo.org/gaia/q2/tsdl/dlget?ID=1866721434011386240&BANDPASS=G
"""

from astropy.io.votable.table import parse as votparse


SAMPLE = votparse("data/vodml-timeseries.xml")

def test_dataset():
    assert (SAMPLE.get_annotations("ds:Dataset")[0].dataProductType
        == "TIMESERIES")


def test_cube():
    cube_ann = SAMPLE.get_annotations("ndcube:Cube")[0]
    assert (set(col.name for col in cube_ann.dependent_axes)
        == {"phot", "flux"})


def test_find_error():
    field_of_interest = SAMPLE.get_first_table(
        ).get_field_by_id_or_name("flux")

    # value points back to itself
    assert field_of_interest.get_annotations(
        "ivoa:Measurement")[0].value.name == "flux"

    assert field_of_interest.get_annotations(
        "ivoa:Measurement")[0].statError.name == "flux_error"


def test_get_target_position():
    target = SAMPLE.get_annotations("ds:Dataset")[0
        ].target
    assert target.type == "ds:AstroTarget"

    for ann in target.position:
        pos_anns = ann.get_annotations("stc2:Coords")
        if pos_anns and pos_anns[0].space.longitude:
            # we've found something we understand
            pos_ann = pos_anns[0]
            break
    
    assert pos_ann.space.frame.orientation == 'ICRS'
    assert pos_ann.space.latitude.name == 'dec'
    assert pos_ann.time.location.name == 'obs_time'


def test_full_position():
    field_of_interest = SAMPLE.get_first_table(
        ).get_field_by_id_or_name("obs_time")

    coord = field_of_interest.get_annotations(
        "stc2:Coords")[0]
    assert abs(coord.space.longitude.value-315.018457397759)<1e-9
    assert coord.time.frame.timescale == "TCB"


COVSAMPLE = votparse("data/covariance.xml")

def test_get_correlated():
    # find all columns that are correlated with pos_RA.
    ra = COVSAMPLE.get_first_table().get_field_by_id_or_name("pos_RA")
    
    # get an error
    err_col = ra.get_annotations("meas2:NaiveMeasurement")[0].error

    # get all correlated errors and collect the (error) columns from
    # their err1 and err2 attributes
    correlated_errors = set()
    for ann in err_col.get_annotations("meas2:Correlation"):
        correlated_errors.add(ann.err1)
        correlated_errors.add(ann.err2)
    
    # and now get the values from all NaiveMeasurements that the errors
    # participate in
    correlated_columns = set()
    for other_err in correlated_errors:
        for ann in other_err.get_annotations("meas2:NaiveMeasurement"):
            correlated_columns.add(ann.value)
    
    corr_names = set(c.name for c in correlated_columns) 
    assert corr_names == {'pos_RA', 'pos_DEC', 'pm_DEC', 
        'RV', 'pm_RA', 'PARALLAX'}, corr_names


if __name__=="__main__":
    for name, obj in globals().copy().items():
        if name.startswith("test_"):
            obj()

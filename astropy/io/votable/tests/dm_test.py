"""
Tests for Markus' (somewhat informal) DM annotation proposal.

Well, actually: I can't be bothered to figure out pytest's setup here, so
for now this is just some sample code; I'll convert it do something 
palatable to pytest when this is going somewhere.
"""

from astropy.io.votable.table import parse as votparse


SAMPLE = votparse("data/vodml-timeseries.xml")

def test_dataset():
    assert (SAMPLE.get_annotations("ds:Dataset")[0].dataProductType[0]
        == "TIMESERIES")

def test_cube():
    assert (set(col.name for col in
            SAMPLE.get_annotations("ndcube:Cube")[0].dependent_axes)==
        {"phot", "flux"})

def test_find_error():
    field_of_interest = SAMPLE.get_first_table(
        ).get_field_by_id_or_name("flux")

    # value points back to itself
    assert field_of_interest.get_annotations(
        "ivoa:Measurement")[0].value[0].name == "flux"

    assert field_of_interest.get_annotations(
        "ivoa:Measurement")[0].statError[0].name, "flux_error"

def test_get_target_position():
    target = SAMPLE.get_annotations("ds:Dataset")[0
        ].target[0]
    assert target.type == "ds:AstroTarget"

    for ann in target.position:
        pos_anns = ann.get_annotations("stc2:SphericalCoordinate")
        if pos_anns and pos_anns[0].longitude:
            # we've found something we understand
            pos_ann = pos_anns[0]
            break
    
    assert pos_ann.frame[0].orientation[0] == 'ICRS'
    assert pos_ann.latitude[0].name == 'dec'


def test_full_position():
    field_of_interest = SAMPLE.get_first_table(
        ).get_field_by_id_or_name("obs_time")

    # Problem: now find the full stc2:Coords annotation(s) this belongs
    # to.  This is currently ugly (essentially, we'd have to iterate
    # though all stc2:Coords instances and see where obs_time is).
    #
    # What should be done: As you declare an annotation for an instance
    # type, we should also declare annotations for types this is being
    # used in.  But that's making a difference between referencing and
    # embedding, which perhaps is lame.  Let's see what tomorrow brings.
    assert False

    
if __name__=="__main__":
    for name, obj in globals().copy().items():
        if name.startswith("test_"):
            obj()

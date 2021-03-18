==========================================
Astropy with Preliminary VO-DML Annotation
==========================================

**Note:**  If you are not a VO nerd (or if you're unsure), this is *not*
the astropy you are looking for.  Head to `astropy trunk`_ right away.

.. _astropy trunk: https://github.com/astropy/astropy

Background
----------

To get an idea on where this is coming from, read `this thread on the IVOA
DM list`_.  Or consider the metaphor Mark CD coined in a github comment:
When building data models, should we be like Lego and deliver the bricks
for people to build whatever they want, possibly the Death Star?  Or
should be deliver the Death Star pre-assembled?

This fork tries to illustrate how the deliver-the-bricks school would
look like.

.. _this thread on the IVOA DM list: http://mail.ivoa.net/pipermail/dm/2020-September/006096.html


Try it out
----------

I'm sure you only want to install this this in a virtual environment –
while it doesn't touch much of astropy, it *is* prototype,
demonstration-level code.  If you are in a virtual environment, simply
running ``python setup.py install`` should do the trick.

There is a sample document annotated with DMs that don't actually exist
in an (overly) minimal annotation scheme in
``astropy/io/votable/tests/data/vodml-timeseries.xml``.  Code exercising
this a bit is in ``astropy/io/votable/tests/dm_test.py``.  As I couldn't
be bothered figuring out some pytest confusion, you can just run this
with normal python; if it runs without output, things haven't regressed.


API
---

The whole DM functionality is exposed through two methods on
*Annotatable*-s (which, in VOTable, are currently RESOURCE, TABLE,
FIELD, and PARAM):

* `get_annotation(dmtype)` -- returns a sequence of annotations of a
  particular VO-DML type (e.g., “give me all positions annotations“).
  Indeed, these are all VO-DML structures the annotatable is, if you
  will, mentioned in.  That is, if an *ra* FIELD is in a
  *stc:SphericalPosition* of a *stc:Coord*, both
  ``ra.get_annotation('stc:SphericalPosition')`` and 
  ``ra.get_annotation('stc:Coord')`` will return something.
* `iter_annotations` -- will iterate over pairs of ``dmtype`` and the
  annoation object.

An annotation is something you can fetch attributes from.  In the
current implementation (``tree.py``), it will always return a list, but
for unknown attributes that list will be empty.  See `Overly Minimal`_
for a critique of this, also I suspect the “default is NULL” policy is
something we should seriously consider for standard APIs in the interest
of easy evolvability.

All annotations are available on the root VOTable.  This allows one to,
for instance, enumerating all “positions” in a VOTable, but in
particular it means that annotations default to annotating the whole
thing, which we use below in the *ds:Dataset* annotation.  I suspect,
however, that DMs actually taking about specific RESOURCEs or TABLEs
should explicitly reference them, as with the *value* attributes in some
of the current annotation.


Use Cases
---------

The primary purpose of this is to show how working with Lego-brick-type
DMs can look like.  Much of the following is ripped from ``dm_test.py``,
except that I'm writing ``vot`` for the parsed VOTable.


Find out a dataset type
'''''''''''''''''''''''

This is in a *ds:Dataset* annotation, which currently is global.
Hence::

  vot.get_annotations("ds:Dataset"  # this returns a list of annotations
    )[0].dataProductType[0]

In the annotation::

    <INSTANCE ID="ndhunnmsbstt" dmtype="ds:Dataset">
        <ATTRIBUTE dmrole="dataProductType">
          <LITERAL dmtype="ivoa:string">TIMESERIES</LITERAL>
        </ATTRIBUTE>
        <ATTRIBUTE dmrole="title">
          <CONSTANT ref="title"/>
        </ATTRIBUTE>
        <ATTRIBUTE dmrole="curation">
          <INSTANCE ID="ndhunnmsbtpa" dmtype="ds:Curation">
            <ATTRIBUTE dmrole="calibLevel">
              <LITERAL dmtype="ivoa:string">1</LITERAL>
  ...

Hence, the value of this will be ``TIMESERIES`` (in gross violation of
http://www.ivoa.net/rdf/product-type, but the instance-generating code
predates that).


Figure out what's smart to plot
'''''''''''''''''''''''''''''''

That's ndcube annotation::

      <INSTANCE ID="ndhunnomdstt" dmtype="ndcube:Cube">
        <ATTRIBUTE dmrole="independent_axes">
          <COLUMN ref="obs_time"/>
        </ATTRIBUTE>
        <ATTRIBUTE dmrole="dependent_axes">
          <COLUMN ref="phot"/>
          <COLUMN ref="flux"/>
        </ATTRIBUTE>
      </INSTANCE>

So, a client filling dialog boxes with suggestions for what to plot on the
abscissa would say::

  vot.get_annotations("ndcube:Cube")[0].independent_axes

and for the ordinate it would be::

  vot.get_annotations("ndcube:Cube")[0].dependent_axes


Establishing the frame for a position
'''''''''''''''''''''''''''''''''''''

To figure out the frame a position is expressed in, take the annotation
on a column that is part of the positional specification and look for
the proper annotation, then use you knowledge of the DM; while you're at
it, also figure out for which epoch the position is given)::

  stc_ann = col.get_annotations("stc2:Coords")[0]
  ref_frame = stc_ann.space[0].frame[0].orientation[0]
  for_epoch = stc_ann.time[0].location

This is based on this annotation::

      <INSTANCE ID="ndhunnmsbset" dmtype="stc2:Coords">
        <ATTRIBUTE dmrole="time">
          <INSTANCE ID="ndhunnmsbhba" dmtype="stc2:TimeCoordinate">
            <ATTRIBUTE dmrole="frame">
              <INSTANCE ID="ndhunnmsbmmt" dmtype="stc2:TimeFrame">
                <ATTRIBUTE dmrole="timescale">
                  <LITERAL dmtype="ivoa:string">TCB</LITERAL>
                </ATTRIBUTE>
                <ATTRIBUTE dmrole="refPosition">
                  <LITERAL dmtype="ivoa:string">BARYCENTER</LITERAL>
                </ATTRIBUTE>
                <ATTRIBUTE dmrole="time0">
                  <LITERAL dmtype="ivoa:string">0</LITERAL>
                </ATTRIBUTE>
              </INSTANCE>
            </ATTRIBUTE>
            <ATTRIBUTE dmrole="location">
              <COLUMN ref="obs_time"/>
            </ATTRIBUTE>
          </INSTANCE>
        </ATTRIBUTE>
        <ATTRIBUTE dmrole="space">
          <INSTANCE ID="ndhunnmsbaut" dmtype="stc2:SphericalCoordinate">
            <ATTRIBUTE dmrole="frame">
              <INSTANCE ID="ndhunnmnonut" dmtype="stc2:SpaceFrame">
                <ATTRIBUTE dmrole="orientation">
                  <LITERAL dmtype="ivoa:string">ICRS</LITERAL>
                </ATTRIBUTE>
                <ATTRIBUTE dmrole="epoch">
                  <LITERAL dmtype="ivoa:string">J2015.5</LITERAL>
                </ATTRIBUTE>
              </INSTANCE>
            </ATTRIBUTE>
            <ATTRIBUTE dmrole="longitude">
              <CONSTANT ref="ra"/>
            </ATTRIBUTE>
            <ATTRIBUTE dmrole="latitude">
              <CONSTANT ref="dec"/>
            </ATTRIBUTE>
          </INSTANCE>
        </ATTRIBUTE>
      </INSTANCE>


Getting an error for a column
'''''''''''''''''''''''''''''

When a client wants to obtain a simple error estimate for a value in a
column ``col``, they would say::

  col.get_annotations("ivoa:Measurement")[0].value[0]

– this gives a literal, a PARAM or a FIELD that contains the error
estimate.  The annotation itself could have further information on
whether that's a 1-sigma or something else, depending on what
*ivoa:Measurement* actually turns out to be in the end.

The annotation used by this (where ``col`` is ``FIELD[@id="flux"]``)::

      <INSTANCE ID="ndhunnomdolt" dmtype="ivoa:Measurement">
        <ATTRIBUTE dmrole="value">
          <COLUMN ref="flux"/>
        </ATTRIBUTE>
        <ATTRIBUTE dmrole="statError">
          <COLUMN ref="flux_error"/>
        </ATTRIBUTE>



Choosing a target position palatable to the client
''''''''''''''''''''''''''''''''''''''''''''''''''

I'm advocating keeping cross-model references at a minimum to avoid
breaking annotation of DM *a* just because a DM *b* it depends on
changes.  For something like the target position in a dataset
annotation, this would mean that it just gives a bunch of columns; the
client then inspects the the annotations of these columns until it finds
one it likes.  First, the underlying annotation::

    <INSTANCE ID="ndhunnmsbstt" dmtype="ds:Dataset">
        ...
        <ATTRIBUTE dmrole="target">
          <INSTANCE ID="ndhunnmsbwha" dmtype="ds:AstroTarget">
            <ATTRIBUTE dmrole="position">
              <CONSTANT ref="ra"/>
              <CONSTANT ref="dec"/>
              <CONSTANT ref="ssa_location"/>
            </ATTRIBUTE>
          </INSTANCE>
        </ATTRIBUTE>

This is what a client could do::

      target = SAMPLE.get_annotations("ds:Dataset")[0
        ].target[0]

      for ann in target.position:
        # this iterates over the fields/params containing the target
        # position
        pos_anns = ann.get_annotations("stc2:Coords")
        if pos_anns:
            # We've found an annotation we understand
            pos_ann = pos_anns[0]
            break
      else:
        raise Exception("Don't understand any target annotation")

The result is a full target annotation with space, time, and frames.


Choosing the most expressive annotation
'''''''''''''''''''''''''''''''''''''''

Continuing the previous example, a client may understand multiple
annotations, say, *stc2:Coords* and a later *stc3:Coords*.  To implement
“use stc3 if present, fall back to stc2 if not”, a client could write::

  pos_ann = None
  for desired_type in ["stc3:Coords", "stc2:Coords"]:
    for ann in ann.get_annotations(desired_type):
      pos_ann = ann

      if pos_ann is not None:
        break

  if pos_ann is None:
    raise Exception("Don't understand any target annotation")
    




Overly Minimal
--------------

The current annotation scheme doesn't keep sequences and scalars apart,
which probably makes this unnecessarily clumsy (though I mention in
passing that this is essentially the metamodel of xpath, and thus we
should at least briefly consider if it's as dumb as it might seem at
first).

It means that all attributes are list-valued, and if you're sure (e.g.,
from the model) you have a scalar, just add a ``[0]``.  As I said, if
I will iterate this, I will quite likely add COLLECTION to the XML
syntax and have scalars and sequences in the annotation, too.

On the other hand, I think I'd drop COLUMN and CONSTANT and just use
@ref on ATTRIBUTE – what's on the other end of a reference is clear by
VOTable, and there's no fundamental difference as to whether that's a
PARAM or a FIELD.


License
-------

Astropy is licensed under a 3-clause BSD style license - see the
`LICENSE.rst <LICENSE.rst>`_ file.

.. |Actions Status| image:: https://github.com/astropy/astropy/workflows/CI/badge.svg
    :target: https://github.com/astropy/astropy/actions
    :alt: Astropy's GitHub Actions CI Status

.. |CircleCI Status| image::  https://img.shields.io/circleci/build/github/astropy/astropy/master?logo=circleci&label=CircleCI
    :target: https://circleci.com/gh/astropy/astropy
    :alt: Astropy's CircleCI Status

.. |Azure Status| image:: https://dev.azure.com/astropy-project/astropy/_apis/build/status/astropy.astropy?repoName=astropy%2Fastropy&branchName=master
    :target: https://dev.azure.com/astropy-project/astropy
    :alt: Astropy's Azure Pipelines Status

.. |Coverage Status| image:: https://codecov.io/gh/astropy/astropy/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/astropy/astropy
    :alt: Astropy's Coverage Status

.. |PyPI Status| image:: https://img.shields.io/pypi/v/astropy.svg
    :target: https://pypi.org/project/astropy
    :alt: Astropy's PyPI Status

.. |Documentation Status| image:: https://img.shields.io/readthedocs/astropy/latest.svg?logo=read%20the%20docs&logoColor=white&label=Docs&version=stable
    :target: https://docs.astropy.org/en/stable/?badge=stable
    :alt: Documentation Status

.. |NumFOCUS| image:: https://img.shields.io/badge/powered%20by-NumFOCUS-orange.svg?style=flat&colorA=E1523D&colorB=007D8A
    :target: http://numfocus.org
    :alt: Powered by NumFOCUS

.. |Donate| image:: https://img.shields.io/badge/Donate-to%20Astropy-brightgreen.svg
    :target: https://numfocus.salsalabs.org/donate-to-astropy/index.html

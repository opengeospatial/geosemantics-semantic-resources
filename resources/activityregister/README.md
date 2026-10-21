# Register of Activity Types Register

This part of this repository contains the content of the OGC's top register of Activity Types, managed by the 
[Geosemantics DWG](https://github.com/opengeospatial/geosemantics-dwg).

> [!WARNING]
> This register is a _candidate_ for Geosemantics DWG management but as of October 2026 is only proposed, 
> not formalised.

This register was established as part of the OGC's
[Open Science Persistent Demonstrator 2026](https://www.ogc.org/initiatives/open-science-persistent-demonstrator-2026/)
project which addressed the provenance of scientific workflows. 

One part of OSPD 2026 was the development of a capability, supported by the OGC, for organizations to create _Activity
Type Registers_ which are managed collections of _activity types_, that is definitions of _types_ of data or other 
processing tasks.

For the cross-register use (querying etc.) of a distributed set of registers that would eventuate from organizations 
creating their own, this top register was created, whose sole job is to register the activity registers.

As per the goal of the OSPD 2026, organizations are free to define whatever kind of activity types the like in their
registers, thus they are the _Register Owner_ of the register and may implement whatever procedures they like, however 
for this top register-of-registers, the OGC is the _Register Owner_, with the Geosemantics DWG nominated as the 
_Register Manager_, and they will follow a process conforming to ISO19135:2026.

## Viewing the register

_(Afer first publication in late October 2026)_ 

This register will be visible online at the Persistent ID location of **<http://w3id.org/ogc/reg/roatr>**.

Technically this register is delivered by the OGC's _Definitions Service_, online at <https://defs.opengis.net>, so the
above link will redirect to this system.

## Adding Registers to this Register

### Conceptual 

To add a Register (an organization's register or Activity types) to this register, the conceptual process is just to 
_submit_ the register details to the _Register Manager_ who will then test the validity of the presented information 
according to the _RIM Model_ (resources/activityregister/models/rim.ttl) and, based on that and other factors such as 
appropriateness of the listing, will approve/reject the submission and, if approved, present the register as a 
_Register Item_ in this register with an appropriate _Item Status_, probably 
[valid](https://def.isotc211.org/codeset/ItemStatus/valid).

Rules for the appropriateness of submissions will be added to the register definition soon.

### Technical

To add a Register to this Register, submit a Pull Request against this repository, targeting the file `roatr.ttl`.

You must:

1. emulate the information in `roatr.ttl` given for the "OGC Activities Register" for your register
2. ensure that your register, wherever published, presents RDF metadata valid according to the RIM Register validator
which is a [SHACL](https://www.w3.org/TR/shacl/) validator and is available in this repository at 
`resources > activityregister > validators > rim-reg.ttl`. It is identified by the IRI 
`<https://w3id.org/ogc/rim/validator/register>`

How to publish a register online isn't explained here: see the 
[OSPD 2026' _Engineering Report_](https://www.w3.org/TR/shacl/) for more info. 

## Contacts
 
To contact the Register Manager of this Register, the Geosemantics DWG, see <https://github.com/opengeospatial/geosemantics-dwg>. 
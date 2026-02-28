from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models import Contact
from app.schemas import IdentifyRequest, ContactResponse, ContactDetails
from fastapi import HTTPException

def identify_contact(db: Session, req: IdentifyRequest) -> ContactResponse:
    if not req.email and not req.phoneNumber:
        raise HTTPException(status_code=400, detail="Either email or phoneNumber must be provided")

    # Step 1: Find Matching Contacts
    query_conditions = []
    if req.email:
        query_conditions.append(Contact.email == req.email)
    if req.phoneNumber:
        query_conditions.append(Contact.phone_number == req.phoneNumber)
        
    matched_contacts = db.query(Contact).filter(or_(*query_conditions)).all()

    # Step 2: If no contacts
    if not matched_contacts:
        new_contact = Contact(
            email=req.email,
            phone_number=req.phoneNumber,
            link_precedence="primary"
        )
        db.add(new_contact)
        db.commit()
        db.refresh(new_contact)
        return build_response(new_contact.id, [new_contact])

    # Step 3: Find all related contacts (Collect Clusters)
    primary_ids = set()
    for c in matched_contacts:
        primary_ids.add(c.id if c.link_precedence == "primary" else c.linked_id)

    # Fetch primary contacts and all their secondaries
    cluster_contacts = db.query(Contact).filter(
        or_(
            Contact.id.in_(primary_ids),
            Contact.linked_id.in_(primary_ids)
        )
    ).all()

    # Step 4: Determine True Primary (Oldest)
    primary_contact = min(
        [c for c in cluster_contacts if c.link_precedence == "primary"],
        key=lambda c: c.created_at
    )

    # Step 5: Handle Merge of Primaries
    for c in cluster_contacts:
        if c.id != primary_contact.id and c.link_precedence == "primary":
            c.link_precedence = "secondary"
            c.linked_id = primary_contact.id
            db.add(c)
        elif c.link_precedence == "secondary" and c.linked_id != primary_contact.id:
            # Also update secondaries of the older primary
            c.linked_id = primary_contact.id
            db.add(c)
            
    db.commit()

    # Re-fetch cluster to get updated state
    cluster_contacts = db.query(Contact).filter(
        or_(
            Contact.id == primary_contact.id,
            Contact.linked_id == primary_contact.id
        )
    ).all()

    # Step 6: Check if New Info Exists
    emails_in_cluster = {c.email for c in cluster_contacts if c.email}
    phones_in_cluster = {c.phone_number for c in cluster_contacts if c.phone_number}

    if (req.email and req.email not in emails_in_cluster) or \
       (req.phoneNumber and req.phoneNumber not in phones_in_cluster):
        new_secondary = Contact(
            email=req.email,
            phone_number=req.phoneNumber,
            linked_id=primary_contact.id,
            link_precedence="secondary"
        )
        db.add(new_secondary)
        db.commit()
        db.refresh(new_secondary)
        cluster_contacts.append(new_secondary)

    # Step 7: Build Response
    return build_response(primary_contact.id, cluster_contacts)

def build_response(primary_id: int, cluster_contacts: list[Contact]) -> ContactResponse:
    emails = []
    phones = []
    secondary_ids = []

    # Get primary first to maintain order
    primary = next((c for c in cluster_contacts if c.id == primary_id), None)
    if primary:
        if primary.email:
            emails.append(primary.email)
        if primary.phone_number:
            phones.append(primary.phone_number)

    for c in cluster_contacts:
        if c.id == primary_id:
            continue
        if c.email and c.email not in emails:
            emails.append(c.email)
        if c.phone_number and c.phone_number not in phones:
            phones.append(c.phone_number)
        
        # Only add secondary IDs
        if c.link_precedence == "secondary":
            secondary_ids.append(c.id)

    return ContactResponse(
        contact=ContactDetails(
            primaryContatctId=primary_id,
            emails=emails,
            phoneNumbers=phones,
            secondaryContactIds=secondary_ids
        )
    )

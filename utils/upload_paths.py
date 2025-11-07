import uuid


def general_upload_to(instance, filename):
    ext = filename.split(".")[-1]
    folder = getattr(instance, "upload_folder", instance.__class__.__name__.lower())
    fk_field_name = getattr(instance, "upload_fk", None)

    if fk_field_name:
        fk_instance = getattr(instance, fk_field_name, None)
        obj_id = getattr(fk_instance, "id", None) or "unassigned"
    else:
        obj_id = getattr(instance, "id", None) or "unassigned"

    return f"{folder}/{obj_id}/{uuid.uuid4()}.{ext}"

class AccessDenied(Exception):
    pass


class ReadAccessDenied(AccessDenied):
    pass


class UpdateAccessDenied(AccessDenied):
    pass


class CreateAccessDenied(AccessDenied):
    pass


class DeleteAccessDenied(AccessDenied):
    pass

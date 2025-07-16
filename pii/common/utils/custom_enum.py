from enum import Enum, EnumMeta

#######################################
#       Custom Enum Metaclass
#######################################

class CustomEnum(EnumMeta):
    """
    Metaclass for enums that adds convenience methods such as names() and search().

    Example:
        class MyEnum(Enum, metaclass=CustomEnum):
            NAME1 = value1
            NAME2 = value2
        MyEnum.names() -> ['NAME1', 'NAME2']
        MyEnum.search('name1') -> MyEnum.NAME1
    """
    def names(cls) -> List[str]:
        """Return a list of member names."""
        return [member.name for member in cls.__members__.values() if isinstance(member, Enum)]

    def values(cls) -> List[Any]:
        """Return a list of member values. """
        return [member.value for member in cls.__members__.values() if isinstance(member, Enum)]

    def search(cls, name: Union[str, int, float]) -> Enum:
        """
        Search for an enum member by name (case-insensitive) or value.

        :param name: The name or value to search for.
        :return: The matching enum member.
        :raises ValueError: If no match is found.
        """
        if isinstance(name, (float, int)):
            name = str(name)
        if not isinstance(name, str):
            raise TypeError(f"Can't use search with value of type '{type(name)}'")
        option = None
        # First check by comparing lowercased names
        if name.lower() in [x.lower() for x in cls.names()]:
            option = cls[name.upper()]
        else:
            # Fallback: compare names and values
            for member in cls.__members__.values():
                try:
                    member_val = str(member.value)
                except Exception:
                    continue
                if member.name.lower() == name.lower() or member_val.lower() == name.lower():
                    option = member
                    break
        if option is None:
            raise ValueError(f"CustomEnum `{cls.__name__}` - No option found for '{name}'")
        return option
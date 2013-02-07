class MD5FormatError(Exception):
    """Error in format of check file"""
    pass


class MD5MatchError(Exception):
    """Computed hash does not match hash in check file"""
    pass


class MD5ReadError(Exception):
    """Error reading file"""
    pass

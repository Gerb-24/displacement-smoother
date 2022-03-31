class Error(Exception):
    """Base class for other exceptions"""
    pass

class NoTopTexture(Error):
    """Raised when we there is no top on a certain stack"""
    pass

class TopTextureUsedForNonDisp(Error):
    """Raised when the toptexture is used on a face without a displacement"""
    pass

class SideTextureUsedForNonDisp(Error):
    """Raised when the sidetexture is used on a face without a displacement"""
    pass

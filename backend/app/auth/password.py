import bcrypt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет соответствие пароля хешу
    
    Args:
        plain_password: Пароль в открытом виде
        hashed_password: Хешированный пароль из БД
        
    Returns:
        True если пароль совпадает, иначе False
    """
    if isinstance(plain_password, str):
        plain_password = plain_password.encode('utf-8')
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
    
    return bcrypt.checkpw(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Хеширует пароль
    
    Args:
        password: Пароль в открытом виде
        
    Returns:
        Хешированный пароль
    """
    if isinstance(password, str):
        password = password.encode('utf-8')
    
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password, salt)
    return hashed.decode('utf-8')

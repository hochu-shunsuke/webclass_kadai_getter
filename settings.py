import json
from cryptography.fernet import Fernet
import getpass

def encode(keyfile):
    key = Fernet.generate_key()
    fernet = Fernet(key)
    
    encrypted = fernet.encrypt(keyfile.encode())
    with open("key.key","wb") as file:
        file.write(key)
        
    with open("userdata.txt","wb") as file:
        file.write(encrypted)

def decode():
    with open("key.key","rb") as file:
        key = file.read()
        
    fernet = Fernet(key)
    
    with open("userdata.txt","rb") as file:
        encrypted = file.read()
        
    decrypted = fernet.decrypt(encrypted)
    
    return decrypted

def decodebydict():
    str = decode()
    d = json.loads(str)
    return d

def getpsw():
    try:
        d = decodebydict()
    except:      
        print("new needs to create.")
        userid = input("userid:")
        password = getpass.getpass("pasword:")
        
        pass_setting = {"userid":userid,"password":password}
        keyfile = json.dumps(pass_setting)
        
        encode(keyfile)
        d = decodebydict()
        
    return d
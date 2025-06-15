class Student:
    def __init__(self, sid, email: str, username: str, password: str, age: int):
        self.sid = sid
        self.email = email
        self.username = username
        self.password = password
        self.age = age

    def getName(self):
        return self.name
    
    def getAge(self):
        return self.age
    
    def getSid(self):
        return self.sid


class Teacher:
    def __init__(self, tid, email: str, username: str, password: str):
        self.tid = tid
        self.email = email
        self.username = username
        self.password = password

    def getTid(self):
        return self.tid
    
    def getEmail(self):
        return self.email

    def getUsername(self):
        return self.username
    
    def getPassword(self):
        return self.password
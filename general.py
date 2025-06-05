import sys
#便利にしたいから
def putlog(str):#プリントの出力先をlog.textに変えてプリントするやつ
    STDOUT = sys.stdout
    fp = open("log.txt","a")
    sys.stdout =  fp
    print(str)
    fp.close()
    sys.stdout = STDOUT

def kugiri():
    print("########################################################")

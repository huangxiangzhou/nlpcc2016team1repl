import sys
import codecs
import re
import json

def removeHFE(kbDict,hfe):
    kbDictCopy = kbDict.copy()
    for key in hfe:
        del kbDictCopy[key]
    return kbDictCopy

def removeHFEFromFile(kbDict,hfePath='hfe.utf8',encode='utf8'):
    hfe = json.load(open(hfePath,'r',encoding=encode))
    kbDictCopy = kbDict.copy()
    for key in hfe:
        del kbDictCopy[key]
    return kbDictCopy


# 高频实体的定义：subject出现在training-set和testing-set中的总共次数在150次以上
def generateHighFreqEntityList(lKey,inputPath1 = 'nlpcc-iccpol-2016.kbqa.training-data',\
                               inputPath2 = 'nlpcc-iccpol-2016.kbqa.testing-data',\
                               outputPath = 'hfe',encode='utf8',threshold = 150):

    fi1=open(inputPath1,'r',encoding=encode)
    fi2=open(inputPath2,'r',encoding=encode)

    fo=open(outputPath+'.'+encode,'w',encoding=encode)

    fotxt=open(outputPath+'.txt','w',encoding=encode)

    entityCountInQ = {}

    listQ = []
    hfe = {}
    
    for line in fi1:
        if line[1] == 'q':
            listQ.append(line[line.index('\t')+1:].strip())
        
    for line in fi2:
        if line[1] == 'q':
            listQ.append(line[line.index('\t')+1:].strip())

    i = 0
    for key in lKey:   
        for qStr in listQ:
            if key in qStr:
                if key in entityCountInQ:
                    entityCountInQ[key] += 1
                else:
                    entityCountInQ[key] = 1
        if key in entityCountInQ and entityCountInQ[key] > threshold:
            hfe[key] = entityCountInQ[key]
        i += 1
        print(str(i),end='\r',flush=True)

    json.dump(hfe,fo)

    for key in hfe:
        fotxt.write(key + ' ||| ' + str(hfe[key]) + '\n')

    fi1.close()
    fi2.close()
    fo.close()
    fotxt.close()
    return hfe
    

def loadKB(path, encode = 'utf8'):
        
    fi = open(path, 'r', encoding=encode)
    prePattern = re.compile(r'[·•\-\s]|(\[[0-9]*\])')


    kbDict={}
    newEntityDic={}
    i = 0
    for line in fi:
        i += 1
        print('exporting the ' + str(i) + ' triple', end='\r', flush=True)
        entityStr = line[:line.index(' |||')].strip()

        tmp = line[line.index('||| ') + 4:]
        relationStr = tmp[:tmp.index(' |||')].strip()
        relationStr, num = prePattern.subn('', relationStr)
        objectStr = tmp[tmp.index('||| ') + 4:].strip()
        if relationStr == objectStr: #delete the triple if the predicate is the same as object
            continue
        if entityStr not in kbDict:
            newEntityDic = {relationStr:objectStr}
            kbDict[entityStr] = []
            kbDict[entityStr].append(newEntityDic)
        else:
            kbDict[entityStr][len(kbDict[entityStr]) - 1][relationStr] = objectStr
            

    fi.close()

    
    return kbDict




def addAliasForKB(kbDictRaw):

    pattern = re.compile(r'[·•\-\s]|(\[[0-9]*\])')

    patternSub = re.compile(r'(\s*\(.*\)\s*)|(\s*（.*）\s*)')  # subject需按照 subject (Description) || Predicate || Object 的方式抽取, 其中(Description)可选

    patternBlank = re.compile(r'\s')

    patternUpper = re.compile(r'[A-Z]')

    patternMark = re.compile(r'《(.*)》')

    kbDict = kbDictRaw.copy()
    for key in list(kbDict):
        if patternSub.search(key):
            keyRe, num = patternSub.subn('', key)
            if keyRe not in kbDict:
                kbDict[keyRe] = kbDict[key]
            else:
                for kb in kbDict[key]:
                    kbDict[keyRe].append(kb)


    for key in list(kbDict):
        match = patternMark.search(key)
        if match:
            keyRe, num = patternMark.subn(r'\1', key)
            if keyRe not in kbDict:
                kbDict[keyRe] = kbDict[key]
            else:
                for kb in kbDict[key]:
                    kbDict[keyRe].append(kb)


    for key in list(kbDict):
        if patternUpper.search(key):
            keyLower = key.lower()
            if keyLower not in kbDict:
                kbDict[keyLower] = kbDict[key]
            else:
                for kb in kbDict[key]:
                    kbDict[keyLower].append(kb)

    for key in list(kbDict):
        if patternBlank.search(key):
            keyRe, num = patternBlank.subn('', key)
            if keyRe not in kbDict:
                kbDict[keyRe] = kbDict[key]
            else:
                for kb in kbDict[key]:
                    kbDict[keyRe].append(kb)
    
    return kbDict   


print('Cleaning kb......')
kbDictRaw = loadKB('nlpcc-iccpol-2016.kbqa.kb')
kbDict = addAliasForKB(kbDictRaw)
json.dump(kbDict, open('kbJson.cleanPre.alias.utf8','w',encoding='utf8'))
print('Removing HFE from kb......')
json.dump(removeHFE(kbDict,generateHighFreqEntityList(list(kbDict))),open('kbJson.cleanPre.alias.NHFE.utf8','w',encoding='utf8'))
print('\nDone!')



#把文本格式的word vector导出成Json格式供后续读入为Python的Dictionary
def convertToJson(inputPath='vectorsw300l20.all', outputPath='vectorJson.utf8'\
                  ,encode = 'utf8'):
    fi = open(inputPath,'r',encoding=encode)

    ll = []
    for line in fi:
        ll.append(line.strip())
    listTmp = []

    embeddingDict = {}
    for i in range(len(ll)-1):
        lineTmp = ll[i+1]
        listTmp = []
        indexSpace = lineTmp.find(' ')
        embeddingDict[lineTmp[:indexSpace]] = listTmp
        lineTmp = lineTmp[indexSpace + 1:]
        for j in range(300):
            indexSpace = lineTmp.find(' ')
            listTmp.append(float(lineTmp[:indexSpace]))
            lineTmp = lineTmp[indexSpace + 1:]



    print('Vector size is ' + str(len(listTmp)))
    print('Dictionary size is ' + str(len(embeddingDict)))
            
    json.dump(embeddingDict,open(outputPath,'w',encoding=encode))

print('Dumping word vector to Json format......')
convertToJson()
print('Done!')



#用训练数据训练答案模板
def getAnswerPatten(inputPath = 'nlpcc-iccpol-2016.kbqa.training-data', outputPath = 'outputAP'):
    inputEncoding = 'utf8'
    outputEncoding = 'utf8'

    fi = open(inputPath, 'r', encoding=inputEncoding)
    fo = open(outputPath, 'w', encoding=outputEncoding)
    foCore = open(outputPath+'.core', 'w', encoding=outputEncoding)

    qRaw = ''

    p1 = re.compile(r'(啊|呀|(你知道)?吗|呢)?(？|\?)*$')
    p2 = re.compile(r'来着')
    p3 = re.compile(r'^呃(……)?')
    p4 = re.compile(r'^请问(一下|你知道)?')
    p5 = re.compile(r'^(那么|什么是|我想知道|我很好奇|有谁了解|问一下|请问你知道|谁能告诉我一下)')
    p6 = re.compile(r'^((谁|(请|麻烦)?你|请|)?(能|告诉)?告诉我)')
    p7 = re.compile(r'^((我想(问|请教)一下)，?)')
    p8 = re.compile(r'^((有人|谁|你|你们|有谁|大家)(记得|知道))')

    lPattern = [p1,p2,p3,p4,p5,p6,p7,p8]

    pattern = re.compile(r'[·•\-\s]|(\[[0-9]*\])') #pattern to clean predicate, in order to be consistent with KB clean method

    APList = {}
    APListCore = {}
    for line in fi:
        if line.find('<q') == 0:  #question line
            qRaw = line[line.index('>') + 2:].strip()
            qRawCore = qRaw
            for p in lPattern:
                qRawCore, num = p.subn('', qRawCore)
            continue
        elif line.find('<t') == 0:  #triple line
            triple = line[line.index('>') + 2:]
            s = triple[:triple.index(' |||')].strip()
            triNS = triple[triple.index(' |||') + 5:]
            p = triNS[:triNS.index(' |||')]
            p, num = pattern.subn('', p)
            if qRaw.find(s) != -1:
                qRaw = qRaw.replace(s,'(SUB)', 1)
           
            qRaw = qRaw.strip() +  ' ||| '  + p

            if qRawCore.find(s) != -1:
                qRawCore = qRawCore.replace(s,'(SUB)', 1)
           
            qRawCore = qRawCore.strip() +  ' ||| '  + p
            if qRaw in APList:
                APList[qRaw] += 1
            else:
                APList[qRaw] = 1

            if qRawCore in APListCore:
                APListCore[qRawCore] += 1
            else:
                APListCore[qRawCore] = 1
        else: continue

    json.dump(APList, fo)

    json.dump(APListCore, foCore)

    fotxt = open(outputPath+'.txt', 'w', encoding=outputEncoding)

    for key in APList:
        fotxt.write(key + ' ' + str(APList[key]) + '\n')
        
    fotxt.close()

    fotxtCore = open(outputPath+'.core.txt', 'w', encoding=outputEncoding)

    for key in APListCore:
        fotxtCore.write(key + ' ' + str(APListCore[key]) + '\n')
        
    fotxtCore.close() 


    fi.close()    
    fo.close()

print('Training answer pattern......')
getAnswerPatten()
print('Done!')



def getCoreQuestion(inputPath = 'nlpcc-iccpol-2016.kbqa.testing-data', encode ='utf8'):
    fi = open(inputPath,'r',encoding=encode)
    fo = open(inputPath+'.core', 'w',encoding=encode)

    p1 = re.compile(r'(啊|呀|(你知道)?吗|呢)?(？|\?)*$')
    p2 = re.compile(r'来着')
    p3 = re.compile(r'^呃(……)?')
    p4 = re.compile(r'^请问(一下|你知道)?')
    p5 = re.compile(r'^(那么|什么是|我想知道|我很好奇|有谁了解|问一下|请问你知道|谁能告诉我一下)')
    p6 = re.compile(r'^((谁|(请|麻烦)?你|请|)?(能|告诉)?告诉我)')
    p7 = re.compile(r'^((我想(问|请教)一下)，?)')
    p8 = re.compile(r'^((有人|谁|你|你们|有谁|大家)(记得|知道))')

    lPattern = [p1,p2,p3,p4,p5,p6,p7,p8]

    for line in fi:
        if line[1] == 'q':
            qRaw = line[line.index('>') + 2:].strip()
            qRawCore = qRaw
            for p in lPattern:
                qRawCore, num = p.subn('', qRawCore)
            fo.write(line.replace(qRaw, qRawCore, 1))
        else:
            fo.write(line)
    fi.close()
    fo.close()
            
        
getCoreQuestion()



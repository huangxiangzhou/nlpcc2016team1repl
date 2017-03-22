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


# 高频实体的定义：if subject出现在training-set中150次以上 and subject出现在testing-set中150次以上  
def generateHighFreqEntityList(lKey,inputPath1 = 'nlpcc-iccpol-2016.kbqa.training-data',\
                               inputPath2 = 'nlpcc-iccpol-2016.kbqa.testing-data',\
                               outputPath = 'hfe',encode='utf8',threshold = 150):

    fi1=open(inputPath1,'r',encoding=encode)
    fi2=open(inputPath2,'r',encoding=encode)

    fo=open(outputPath+'.'+encode,'w',encoding=encode)

    fotxt=open(outputPath+'.txt','w',encoding=encode)

    entityCountInTrainingQ = {}
    entityCountInTestingQ = {}
    listTrainingQ = []
    listTestingQ = []
    hfe = {}

    for line in fi1:
        if line[1] == 'q':
            listTrainingQ.append(line[line.index('\t')+1:].strip())
        
    for line in fi2:
        if line[1] == 'q':
            listTestingQ.append(line[line.index('\t')+1:].strip())

    i = 0
    for key in lKey:   
        for qStr in listTrainingQ:
            if key in qStr:
                if key in entityCountInTrainingQ:
                    entityCountInTrainingQ[key] += 1
                else:
                    entityCountInTrainingQ[key] = 1
        if key in entityCountInTrainingQ and entityCountInTrainingQ[key] > threshold:
            for qStr in listTestingQ:
                if key in qStr:
                    if key in entityCountInTestingQ:
                        entityCountInTestingQ[key] += 1
                    else:
                        entityCountInTestingQ[key] = 1
            if key in entityCountInTestingQ and entityCountInTestingQ[key] > threshold:
                hfe[key] = [entityCountInTrainingQ[key],entityCountInTestingQ[key]]
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
    pattern = re.compile(r'[·•\-\s]|(\[[0-9]*\])')

    kbDict={}
    newEntityDic={}
    i = 0
    for line in fi:
        i += 1
        print('exporting the ' + str(i) + ' triple', end='\r', flush=True)
        entityStr = line[:line.index(' |||')].strip()
        tmp = line[line.index('||| ') + 4:]
        relationStr = tmp[:tmp.index(' |||')].strip()
        relationStr, num = pattern.subn('', relationStr)
        objectStr = tmp[tmp.index('||| ') + 4:].strip()
        if entityStr not in kbDict:
            newEntityDic = {relationStr:objectStr}
            kbDict[entityStr] = []
            kbDict[entityStr].append(newEntityDic)
        else:
            kbDict[entityStr][len(kbDict[entityStr]) - 1][relationStr] = objectStr
            

    fi.close()
    return kbDict

print('Cleaning kb......')
kbDict = loadKB('nlpcc-iccpol-2016.kbqa.kb')
json.dump(removeHFE(kbDict,generateHighFreqEntityList(list(kbDict))),open('kbJson.cleanPre.NHFE.utf8','w',encoding='utf8'))
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
def getAnswerPatten(inputPath = 'nlpcc-iccpol-2016.kbqa.training-data', outputPath = 'outputAP', qCore = False):
    inputEncoding = 'utf8'
    outputEncoding = 'utf8'

    fi = open(inputPath, 'r', encoding=inputEncoding)
    fo = open(outputPath, 'w', encoding=outputEncoding)

    qRaw = ''

    p1 = re.compile(r'(啊|呀|(你知道)?吗|呢)?(？|\?)*$')
    p2 = re.compile(r'来着')
    p3 = re.compile(r'^呃(······)?')
    p4 = re.compile(r'^请问(一下|你知道)?')
    p5 = re.compile(r'^(那么|什么是|我想知道|我很好奇|有谁了解|问一下|请问你知道|谁能告诉我一下)')
    p6 = re.compile(r'^((谁|(请|麻烦)?你|请|)?(能|告诉)?告诉我)')
    p7 = re.compile(r'^((我想(问|请教)一下)，?)')
    p8 = re.compile(r'^((有人|谁|你|你们|有谁|大家)(记得|知道))')

    lPatten = [p1,p2,p3,p4,p5,p6,p7,p8]

    pattern = re.compile(r'[·•\-\s]|(\[[0-9]*\])') #pattern to clean predicate, in order to be consistent with KB clean method

    APList = {}
    for line in fi:
        if line.find('<q') == 0:  #question line
            qRaw = line[line.index('>') + 2:].strip()
            if qCore == True:
                for patten in lPatten:
                    qRaw, num = patten.subn('', qRaw)
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
            if qRaw in APList:
                APList[qRaw] += 1
            else:
                APList[qRaw] = 1
        else: continue

    json.dump(APList, fo)

    fo2 = open(outputPath+'.txt', 'w', encoding=outputEncoding)

    for key in APList:
        fo2.write(key + ' ' + str(APList[key]) + '\n')
        
    fo2.close() 


    fi.close()    
    fo.close()

print('Training answer pattern......')
getAnswerPatten()
print('Done!')

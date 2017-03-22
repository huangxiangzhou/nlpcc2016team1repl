import sys
import codecs
import lcs   #the lcs module is in extension folder
import time
import json



class answerCandidate:
    def __init__(self, sub = '', pre = '', qRaw = '', qType = 0, score = 0, kbDict = [], wS = 1, wP = 10, wAP = 100):
        self.sub = sub     
        self.pre = pre     
        self.qRaw = qRaw     
        self.qType = qType
        self.score = score
        self.kbDict = kbDict
        self.origin = ''
        self.scoreDetail = [0,0,0,0,0]
        self.wS = wS
        self.wP = wP
        self.wAP = wAP
        self.scoreAP = 0
        self.scorePre = 0
        

    def calcScore(self, qtList, vectorDict, debug=False):
        scoreSub = len(self.sub)
        scorePre = 0
        scoreAP = 0
        pre = self.pre
        qWithoutSub = self.qRaw.replace(self.sub,'',1)
        qtKey = (self.qRaw.replace(self.sub,'(SUB)',1) + ' ||| ' + pre)
        if qtKey in qtList:
            scoreAP = qtList[qtKey]
                    
        self.scoreAP = scoreAP
        

        segListPre = []
        
        lenPre = len(pre)

        lenPreSum = 0
        for i in range(lenPre):
            for j in range(lenPre):
                if i+j < lenPre:
                    preWordTmp = pre[i:i+j+1]
                    if preWordTmp in vectorDict:
                        segListPre.append(preWordTmp)
                        lenPreSum += len(preWordTmp)
            
        
        lenQNS = len(qWithoutSub)
        segListQNS = []
        for i in range(lenQNS):
            for j in range(lenQNS):
                if i+j < lenQNS:
                    QNSWordTmp = qWithoutSub[i:i+j+1]
                    if QNSWordTmp in vectorDict:
                        segListQNS.append(QNSWordTmp)	
        # Add Question type rules, ref to Table.1 in the article                
        if qWithoutSub.find('什么时候') != -1 or qWithoutSub.find('何时') != -1:
            segListQNS.append('日期')
            segListQNS.append('时间')			
        if qWithoutSub.find('在哪') != -1:
            segListQNS.append('地点')
            segListQNS.append('位置')			
        if qWithoutSub.find('多少钱') != -1:
            segListQNS.append('价格')
            
        for preWord in segListPre:
            scoreMaxCosine = 0
            for QNSWord in segListQNS:
                cosineTmp = lcs.cosine(vectorDict[preWord],vectorDict[QNSWord])
                if cosineTmp > scoreMaxCosine:
                    scoreMaxCosine = cosineTmp
            scorePre += scoreMaxCosine * len(preWord)

        if lenPreSum == 0:
            scorePre = 0
        else:
            scorePre = scorePre / lenPreSum
        

        self.scorePre = scorePre

        self.score = scoreSub * self.wS + scorePre * self.wP + scoreAP * self.wAP
        
        return self.score

def getAnswer(sub, pre, kbDict):
    for kb in kbDict[sub]:
        if pre in kb:
            return kb[pre]
    return 'NO ANSWER FOUND BY QA SYSTEM'

    



def answerQ (qRaw, lKey, kbDict, qtList, vectorDict, threshold=0, debug=False):
    q = qRaw.strip()
    
    candidateSet = set()
    
    result = ''

 
    maxScore = 0

    bestAnswer = set()

    # Get all the candidate triple
    for key in lKey:
        if -1 != q.find(key):
            for kb in kbDict[key]:
                for pre in list(kb):
                    newAnswerCandidate = answerCandidate(key, pre, q)
                    candidateSet.add(newAnswerCandidate)
   
    
    
    candidateSetCopy = candidateSet.copy()
    if debug:
        print('len(candidateSet) = ' + str(len(candidateSetCopy)), end = '\r', flush=True)
    candidateSet = set()

    candidateSetIndex = set()

    for aCandidate in candidateSetCopy:
        strTmp = str(aCandidate.sub+'|'+aCandidate.pre)
        if strTmp not in candidateSetIndex:
            candidateSetIndex.add(strTmp)
            candidateSet.add(aCandidate)


    for aCandidate in candidateSet:
        scoreTmp = aCandidate.calcScore(qtList, vectorDict,debug)
        if scoreTmp > maxScore:
            maxScore = scoreTmp
            bestAnswer = set()
        if scoreTmp == maxScore:
            bestAnswer.add(aCandidate)
            


            
    bestAnswerCopy = bestAnswer.copy()
    bestAnswer = set()
    for aCandidate in bestAnswerCopy:
        aCfound = 0
        for aC in bestAnswer:
            if aC.pre == aCandidate.pre and aC.sub == aCandidate.sub:
                aCfound = 1
                break
        if aCfound == 0:
            bestAnswer.add(aCandidate)
            
            
    if debug:
        for ai in bestAnswer:
            for kb in kbDict[ai.sub]:
                if ai.pre in kb:
                    print(ai.sub + ' ' +ai.pre + ' '+ kb[ai.pre])
        return[bestAnswer,candidateSet]       
    else:
        return bestAnswer
        


def loadQtList(path, encode = 'utf8'):
    qtList = json.load(open(path,'r',encoding=encode))

    return qtList

def loadVectorDict(path, encode = 'utf8'):
    vectorDict = json.load(open(path,'r',encoding=encode))

    return vectorDict       

def answerAllQ(pathInput, pathOutput, lKey, kbDict, qtList, vectorDict, qIDstart=1):
    fq = open(pathInput, 'r', encoding='utf8')
    i = qIDstart
    timeStart = time.time()
    fo = open(pathOutput, 'w', encoding='utf8')
    fo.close()
    listQ = []
    for line in fq:
        if line[1] == 'q':
            listQ.append(line[line.index('\t')+1:].strip())
    for q in listQ:
        fo = open(pathOutput, 'a', encoding='utf8')
        result = answerQ(q, lKey, kbDict, qtList, vectorDict)
        fo.write('<question id='+str(i)+'>\t' + q + '\n')
        if len(result) != 0:
            answerSet = set()
            fo.write('<triple id='+str(i)+'>\t')
            for res in result:
                answerTmp = getAnswer(res.sub, res.pre, kbDict)
                answerSet.add(answerTmp)
                fo.write(res.sub + ' ||| ' + res.pre + ' ||| '\
                         + answerTmp  + ' ||| ' + str(res.score) + ' ====== ')
            fo.write('\n')
            fo.write('<answer id='+str(i)+'>\t')
            for ansTmp in answerSet:
                fo.write(ansTmp)
                if len(answerSet) > 1:
                    fo.write(' ||| ')
            fo.write('\n==================================================\n')
        else:
            fo.write('<triple id='+str(i)+'>\t')
            fo.write('\n')
            fo.write('<answer id='+str(i)+'>\t')
            fo.write('\n==================================================\n')
        print('processing ' + str(i) + 'th Q.\tAv time cost: ' + str((time.time()-timeStart) / i)[:6] + ' sec', end = '\r', flush=True)
        fo.close()
        i += 1
    fq.close()       
    

def loadResAndanswerAllQ(pathInput, pathOutput, pathDict, pathQt, pathVD, encode='utf8', qIDstart=1):
    print('Start to load kbDict from json format file: ' + pathDict)
    kbDict = json.load(open(pathDict, 'r', encoding=encode))
    print('Loaded kbDict completely! kbDic length is '+ str(len(kbDict)))
    qtList = loadQtList(pathQt, encode)
    print('Loaded qtList completely! qtList length is '+ str(len(qtList)))
    vectorDict = loadVectorDict(pathVD)
    print('Loaded vectorDict completely! vectorDict length is '+ str(len(vectorDict)))
    answerAllQ(pathInput, pathOutput, list(kbDict), kbDict, qtList, vectorDict, qIDstart=1)




if len(sys.argv) == 7:
    pathInput=sys.argv[1]
    pathOutput=sys.argv[2]
    pathDict=sys.argv[3]
    pathQt=sys.argv[4]
    pathVD=sys.argv[5]
    qIDstart=int(sys.argv[6])
    loadResAndanswerAllQ(pathInput, pathOutput, pathDict, pathQt, pathVD, 'utf8', qIDstart)

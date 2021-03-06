import pymongo
import re

class DataSetMeasure:
    def __init__(self, name, collCandidate, collValid, collRelCandidate, collRelValid, collTypeCandidate, collTypeValid, collLabelsCandidate, collLabelsValid):
        self.name = name
        #print("Connecting to mongoDB (localhost) server...")
        client = pymongo.MongoClient("localhost", 27017)
        db = client.valRKB
        self.collCandidate = db[collCandidate]
        self.collValid = db[collValid]
        
        self.collRelValid = db[collRelValid]
        self.collRelCandidate = db[collRelCandidate]
        self.collTypeCandidate = db[collTypeCandidate]
        self.collTypeValid = db[collTypeValid]
        self.collLabelsCandidate = db[collLabelsCandidate]
        self.collLabelsValid = db[collLabelsValid]
        #print "Connected to "+db.name+"!"
        self.nbValidate = 0
        self.nbCandidate = 0
        
        self.nbRelValidate = 0
        self.nbRelCandidate = 0
        
        self.nbTaxonValidate = 0
        self.nbTaxonCandidate = 0
        self.precision = -1
        self.recall = -1
    def getName(self):
        return self.name
    def getPrecision(self, trustScore, limitNbValidator):
        for item in self.collCandidate.find({"trustScore" : {"$gt": trustScore}}):
            self.nbCandidate += 1
            #print item["elemCandidates"]
            #print"\t\t\t --> "+str(item["trustScore"])
            allValid = True
            for elem in item["elemCandidates"]:
                validElem = self.collValid.find_one({"uri": elem})
                if(validElem != None):
                    #print validElem
                    if((validElem["nbVal"] >= limitNbValidator) and (validElem["nbNotVal"] == 0)):
                        #print "\t VALIDATE : "+elem+" --> "+str(validElem["nbVal"])
                        loutre = 42
                    else:
                        #print"\t NOT VALIDATE!"+elem+"(nbVal:"+str(validElem["nbVal"])+", nbNotVal:"+str(validElem["nbNotVal"])+", nbDontKnow:"+str(validElem["nbDontKnow"])+")"
                        allValid = False
                else:
                    allValid = False
                    #print "\t NOT VALIDATE!"+elem+" (not exists)"
                
            if(allValid):
                self.nbValidate +=1
                
        #print "Nb validate :"+str(self.nbValidate)
        #print "Nb candidate : "+str(self.nbCandidate)
        print str(self.nbValidate)+ " / "+str(self.nbCandidate)
        self.precision = float(self.nbValidate)/float(self.nbCandidate)
        return self.precision
    def getRecall(self, limitTrustScore, limitNbValidators):
        for item in self.collValid.find():
            if((item["nbVal"] >= limitNbValidators) and (item["nbNotVal"] == 0)):
                self.nbTaxonValidate += 1
#                 print "TEST : "+item['uri']+": "
                for elem in self.collCandidate.find({'elemCandidates' : item["uri"]}):
                    if(elem['trustScore'] > limitTrustScore):
    #                     print "\t("+str(elem['trustScore'])+" -->"
    #                     print elem['elemCandidates']
                        self.nbTaxonCandidate +=1
                        break
        print str(self.nbTaxonCandidate)+" / "+str(self.nbTaxonValidate)
        self.recall =float(self.nbTaxonCandidate)/float(self.nbTaxonValidate) 
        return self.recall
    def __getUriFromSource(self, ic, source):
        ret = None
        for elem in ic:
            if(elem["source"] == source):
                ret = elem["uri"]
                break
        return ret
    def getPrecisionRelation(self, trustScore, limitNbValidator):
        relCandidate = 0
        relCandidateValidated = 0
        for item in self.collRelCandidate.find({"trustScore" : {"$gt": trustScore}}):
            relCandidate += 1
            allValid = True
            ic = item["ic"]
            icHR = item["icHR"]
            for elem in ic:
                uri = elem["uri"]
                source = elem["source"]
                uriHR = self.__getUriFromSource(icHR, source)
                if(uriHR != None):
                    uriRel = "&lt;"+uri+"&gt; &lt;http://ontology.irstea.fr/AgronomicTaxon#hasHigherRank&gt; &lt;"+uriHR+"&gt;"
                    validElem = self.collRelValid.find_one({"uri": uriRel})
                    if(validElem != None):
                        if((validElem["nbVal"] >= limitNbValidator) and (validElem["nbNotVal"] == 0)):
                            loutre = 42
                        else:
                            allValid = False
                    else:
                        allValid = False

            if(allValid):
                relCandidateValidated +=1
        print str(relCandidateValidated)+ " / "+str(relCandidate)
        precisionRel = float(relCandidateValidated)/float(relCandidate)
        return precisionRel
    def __findSubString(self, raw_string, start_marker, end_marker):
        return raw_string[raw_string.find(start_marker)+4:raw_string.find(end_marker)]
    def __findSubStringLast(self, raw_string, start_marker, end_marker):
        return raw_string[raw_string.rfind(start_marker)+4:raw_string.rfind(end_marker)]
    def getRecallRelation(self, limitTrustScore, limitNbValidators):
        nbRelValidate = 0
        nbRelCandidate = 0
        for item in self.collRelValid.find():
            if((item["nbVal"] >= limitNbValidators) and (item["nbNotVal"] == 0)):
                nbRelValidate += 1
                uri1 = self.__findSubString(item["uri"], "&lt;", "&gt;")
                uri2 =  self.__findSubStringLast(item["uri"], "&lt;", "&gt;")
                for elem in self.collRelCandidate.find({"ic":{"$elemMatch":{"uri" : uri1} }, "icHR":{"$elemMatch":{"uri":uri2}}}):
                    if(elem['trustScore'] > limitTrustScore):
                        nbRelCandidate +=1
                        break
        print str(nbRelCandidate)+" / "+str(nbRelValidate)
        self.recall =float(nbRelCandidate)/float(nbRelValidate) 
        return self.recall
    def getPrecisionType(self, trustScore, limitNbValidator):
        typeCandidate = 0
        typeCandidateValidated = 0
        for item in self.collTypeCandidate.find({"trustScore" : {"$gt": trustScore}}):
            typeCandidate += 1
            allValid = True
            ic = item["ic"]
            typeUri = item["typeURI"]
            if(typeUri != None):
                for elem in ic:
                    uri = elem["uri"]
                    #source = elem["source"]
                    uriValidation = "&lt;"+uri+"&gt; a &lt;"+typeUri+"&gt;"
                    validElem = self.collTypeValid.find_one({"uri": uriValidation})
                    if(validElem != None):
                        if((validElem["nbVal"] >= limitNbValidator) and (validElem["nbNotVal"] == 0)):
                            loutre = 42
                        else:
                            allValid = False
                    else:
                        allValid = False
            else:
                allValid = False

            if(allValid):
                typeCandidateValidated +=1
        print str(typeCandidateValidated)+ " / "+str(typeCandidate)
        precisionType = float(typeCandidateValidated)/float(typeCandidate)
        return precisionType
    def getRecallType(self, limitTrustScore, limitNbValidators):
        nbTypeValidate = 0
        nbTypeCandidate = 0
        for item in self.collTypeValid.find():
            if((item["nbVal"] >= limitNbValidators) and (item["nbNotVal"] == 0)):
                nbTypeValidate += 1
                uri = self.__findSubString(item["uri"], "&lt;", "&gt;")
                uriType =  self.__findSubStringLast(item["uri"], "&lt;", "&gt;")
                for elem in self.collTypeCandidate.find({"ic":{"$elemMatch":{"uri" : uri} }, "typeURI" : uriType}):
                    if(elem['trustScore'] > limitTrustScore):
                        nbTypeCandidate +=1
                        break
        print str(nbTypeCandidate)+" / "+str(nbTypeValidate)
        self.recall =float(nbTypeCandidate)/float(nbTypeValidate) 
        return self.recall
    def __getLabelFromSource(self, labels, source):
        ret = None
        for elem in labels:
            if(elem["source"] == source):
                ret = elem["label"]
                break
        return ret
    def getPrecisionLabels(self, trustScore, limitNbValidator):
        labelsCandidate = 0
        labelsCandidateValidated = 0
        testInt = 0
        for item in self.collLabelsCandidate.find({"trustScore" : {"$gt": trustScore}}):
            testInt += 1
            labelsCandidate += 1
            allValid = True
            ic = item["ic"]
            for elem in ic:
                uri = elem["uri"]
                source = elem["source"]
                label = self.__getLabelFromSource(item["labels"], source)
                #print "Label ("+str(testInt)+") : "+uri+"("+source+") -> "+label
                if(label != None):
                    uriValidation = uri.replace("?", "\?").replace(".", "\.")
                    regexpVar = "^&lt;"+uriValidation+"&gt;.*"+label+"[\.,\[]"
                    validElem = self.collLabelsValid.find_one({'uri':{'$regex': regexpVar}})
                    if(validElem != None):
                        if((validElem["nbVal"] >= limitNbValidator) and (validElem["nbNotVal"] == 0)):
                            loutre = 42
                        else:
                            allValid = False
                    else:
                        allValid = False
            if(allValid):
                labelsCandidateValidated +=1
        print str(labelsCandidateValidated)+ " / "+str(labelsCandidate)
        if(labelsCandidateValidated > 0 and labelsCandidate > 0):
            precisionLabels = float(labelsCandidateValidated)/float(labelsCandidate)
        else:
            precisionLabels = 0
        return precisionLabels
    def getRecallLabels(self, limitTrustScore, limitNbValidators):
        nbLabelValidate = 0
        nbLabelCandidate = 0
        for item in self.collLabelsValid.find():
            if((item["nbVal"] >= limitNbValidators) and (item["nbNotVal"] == 0)):
                validUri = item["uri"]
                uri = self.__findSubString(validUri, "&lt;", "&gt;")
                uriVal = uri.replace("?", "\?").replace(".", "\.")
                for s in re.findall(r"&lt;"+uriVal+"&gt; rdfs:label\(\w+\) ([^&]+)", validUri, re.UNICODE):
                    for sLabel in s.split(","):
                        nbLabelValidate += 1
                        sLabel = sLabel.strip()
                        if "[" in sLabel:
                            sLabel = sLabel[0:sLabel.find("[")]
                        if sLabel.endswith("."):
                            sLabel = sLabel.strip(".")
                        for elem in self.collLabelsCandidate.find({"ic":{"$elemMatch":{"uri": uri}}, "labels":{"$elemMatch":{"label":sLabel}}}):
                            if(elem['trustScore'] > limitTrustScore):
                                nbLabelCandidate +=1
                                break
        print str(nbLabelCandidate)+" / "+str(nbLabelValidate)
        if (nbLabelCandidate > 0 and nbLabelValidate > 0):
            recallLabels =float(nbLabelCandidate)/float(nbLabelValidate)
        else:
            recallLabels = 0  
        return recallLabels
    def removeCollCandidate(self):
        self.collCandidate.remove({})
    def removeCollValid(self):
        self.collValid.remove({})

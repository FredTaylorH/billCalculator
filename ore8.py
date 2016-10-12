import csv
import datetime
import operator
#import oreUnitTest

def convertDate(file,field,format):
	for datapoint in file:
		datapoint[field] = datetime.datetime.strptime(datapoint[field],format)

def convertStringToFloat(dataset,listOfFields):
	for row in dataset:
		#print('row is: ' , row)
		for field in listOfFields:
			row[field] = float(row[field])
	return(dataset)

def dateRangeLookup(compoundKey,dictionariesToSearch,dateField,first,last,valueToReturn,dictToUpdate):
	'''
	FOR RATES
	Looks for a (dict) in a list of dictionariesToSearch.
	If in finds that dict in the list of dictionariesToSearch,
	AND the date is in a daterange, 
	update dictToUpdate with valueToReturn.
	Note: This is only built to find one key-value pair to return
	Modify object in place, does not return anything
	'''
	for eachDictionary in dictionariesToSearch:
		if compoundKey.items() <= eachDictionary.items() and dateField >= eachDictionary[first] and dateField < eachDictionary[last]: #Left endpoint convention
			dictToUpdate[valueToReturn] = eachDictionary[valueToReturn]

def sumBetweenDates(listOfDictionaries,dateField,fieldToSum,first,last):
	total = 0
	for eachDictionary in listOfDictionaries:
		if eachDictionary[dateField] >= first and eachDictionary[dateField] < last: #Left endpoint
			total = total + eachDictionary[fieldToSum]
	return(total)
			
#Read in csv as a list of dictionaries. Each row is an element in the list. 
def readInCsv(file,subsetField=None,subsetObservation=None):
	data = []
	with open(file) as f:
		for row in csv.DictReader(f, skipinitialspace=True):
			observation = {key : value for key , value in row.items()}
			data.append(observation)
		if subsetField != None and subsetObservation !=None:
			data = [i for i in data if i[subsetField] == subsetObservation]
		return(data)		
		
def lookup(compoundKey,dictionariesToSearch,valueToReturn,dictToUpdate):
	'''
	Looks for a (dict) in a list of dictionariesToSearch.
	If in finds that dict in the list of dictionariesToSearch,
	update dictToUpdate with valueToReturn.
	Note: This is only built to find one key-value pair to return	
	RETURN ALL OTHER FIELDS?
	'''
	for eachDictionary in dictionariesToSearch:
		if compoundKey.items() <= eachDictionary.items():
			dictToUpdate[valueToReturn] = eachDictionary[valueToReturn]
	#return(dictToUpdate)	
	
def makeListFromDictionaryEntries(targetDictionary,listOfKeys):
	newList = []
	for key in listOfKeys:
		newList.append(float(targetDictionary[key]))
	return(newList)
	
def calculateStandardUtilityBill(usage,cumulativeCutoffsList,lengthInDays,allowancePerDay,nonCumulativeCutoffsList,tierPriceList,genRate,fixedCharges):
	'''
	Note: Does not include PPA
	'''
	absoluteValueKwh = abs(usage)
	sign = (usage > 0) - (usage < 0)
	
	highestTier = 0 #Get highest tier
	for cutoff in cumulativeCutoffsList:
		if (cutoff * lengthInDays * allowancePerDay) <= absoluteValueKwh :
			highestTier+=1
			
	fullTiersKwh = [] #Get kWh in n full Tiers and 1 partial tier
	for tier in range(1,highestTier):
			fullTiersKwh.append(nonCumulativeCutoffsList[tier] * lengthInDays * allowancePerDay)
	partialTierKwh = absoluteValueKwh - sum(fullTiersKwh)
	
	#Get each bill component
	fullTiersBill = sum([a*b for a,b in zip(tierPriceList,fullTiersKwh)])	
	partialTierBill = partialTierKwh * tierPriceList[highestTier-1]	
	generationBill = (genRate*absoluteValueKwh)
	fixedChargeBill = (lengthInDays*fixedCharges)

	#Get total bill
	totalUtilityBill = sign * (fullTiersBill + partialTierBill + generationBill + fixedChargeBill)
	#print('Standard bill is: ',totalUtilityBill)
	
	return (totalUtilityBill)


def calculateSpecialExportUtilityBill(usage,specialExportRate,lengthInDays,fixedCharges):	#Applies to EversourceMA customers
	totalUtilityBill = (usage*specialExportRate) + (lengthInDays*fixedCharges)
	#print('Export bill is: ',totalUtilityBill)
	return(totalUtilityBill)
	
def calculateFixedChargeOnlyUtilityBill(lengthInDays,fixedCharges):
	totalUtilityBill = lengthInDays*fixedCharges
	#print('Fixed Charge only bill is:',totalUtilityBill)
	return(totalUtilityBill)


def calculateSolarPpaBill(ppa,solarProduction):
	solarPpaBill = (ppa *  solarProduction)
	return(solarPpaBill)	
	

def calculatePostSolarTrueUpBill(totalAnnualUsage,totalAnnualUtilityBill,nscDeterminant,nscRate):
	if (nscDeterminant=='kWh' and totalAnnualUsage<0) or (nscDeterminant=='dollars' and totalAnnualUtilityBill<0):
		postSolarTrueUpBill = totalAnnualUsage * nscRate + max(totalAnnualUtilityBill,cumulativePostSolarCurrentCharges) #This max() ensures that the user pays at least the minimum charges.
		#print('User has NSC of: ',postSolarTrueUpBill)
	else:
		#postSolarTrueUpBill = max(totalAnnualUtilityBill,cumulativePostSolarCurrentCharges) #This max() ensures that the user pays at least the minimum charges for the CA IOU's.
		postSolarTrueUpBill = totalAnnualUtilityBill
		#print('User does not receive NSC')
	return(postSolarTrueUpBill)

		
#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
#STEP 1: Create customer with all the information we need to calculate the bill, pulled in from CSV databases
#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

#Specify fields we are interested in reading from the CSV, list of customers we want to calculate bills for, and make a list to hold the results.
allRatesFields = ['fixedCharges','isCumulativeCutoff1','isCumulativeCutoff2','isCumulativeCutoff3','isCumulativeCutoff4','isCumulativeCutoff5','tierPrice1','tierPrice2','tierPrice3','tierPrice4','tierPrice5','nonCumulativeCutoff1','nonCumulativeCutoff2','nonCumulativeCutoff3','nonCumulativeCutoff4','nonCumulativeCutoff5']
cumulativeCutoffFields = ['isCumulativeCutoff1','isCumulativeCutoff2','isCumulativeCutoff3','isCumulativeCutoff4','isCumulativeCutoff5']
nonCumulativeCutoffFields = ['nonCumulativeCutoff1','nonCumulativeCutoff2','nonCumulativeCutoff3','nonCumulativeCutoff4','nonCumulativeCutoff5']
tierPriceFields = ['tierPrice1','tierPrice2','tierPrice3','tierPrice4','tierPrice5']
infoFields = ['utility','state','rateSchedule','ppa']
nemRulesFields = ['billOnStandardRateInAllMonths','fixedChargeForNegativeKwh','specialExportRate','nscDeterminant','nscRate']

customersOfInterest = [{'customer':'indrahall@gmail.com'},{'customer':'barokninja@yahoo.com'},{'customer':'spinkham@yahoo.com'},{'customer':'michel.pierre70@gmail.com'}]
allResults = []


#Readin and format. Two way-looping over customers and bills; we have a list of n customers, each having m (usually 12) bills 
for customerOfInterest in customersOfInterest:

	#Read in all csv's. Only keep the bills and solar data we care about, for performance.
	customerBills        = readInCsv('oreBills_test.csv','customer',customerOfInterest['customer'])
	customerSolarData    = readInCsv('oreSolarIntervals_test.csv','customer',customerOfInterest['customer'])
	info                 = readInCsv('oreCustomerInfo_test.csv')
	rates                = readInCsv('oreRates_test.csv')
	seasons              = readInCsv('oreSeasons_test.csv')
	nemRules             = readInCsv('oreNemRules_test.csv')


	#Convert strings to floats, as appropriate, and strings to dates, as appropriate.
	convertStringToFloat(customerBills,['allowance','postSolarNetKwh','genRate','exportCredit','currentCharges','nscDisbursed','nemChargesBeforeTaxes'])
	convertStringToFloat(customerSolarData,['kWh'])
	convertStringToFloat(info,['ppa'])
	convertStringToFloat(rates,allRatesFields)
	convertStringToFloat(seasons,['month'])
	convertStringToFloat(nemRules,['billOnStandardRateInAllMonths','specialExportRate','fixedChargeForNegativeKwh','nscRate'])

	convertDate(customerSolarData,'cleanDate','%Y%m%d')
	convertDate(customerBills,'billStart','%Y%m%d')
	convertDate(customerBills,'billEnd','%Y%m%d')
	convertDate(rates,'realStart','%Y%m%d')
	convertDate(rates,'realEnd','%Y%m%d')

	#Make the complete customer-bill dictionary by 1) calculating fields and 2) doing lookups on a key.
	for bill in customerBills:
		
		#Calculate / change type of fields we will need to do billCalcs
		bill['midpointDate'] = bill['billStart'] + (bill['billEnd'] - bill['billStart'])/2
		bill['lengthInDays'] = (bill['billEnd'] - bill['billStart']).days
		bill['month'] = bill['midpointDate'].month 
		bill['allowancePerDay'] = bill['allowance'] / bill['lengthInDays']
		bill['postSolarSolarProduction'] = sumBetweenDates(customerSolarData,'cleanDate','kWh',bill['billStart'],bill['billEnd']) 
		bill['preSolarSolarProduction'] = 0
		bill['preSolarGrossKwh'] = bill['postSolarNetKwh'] + bill['postSolarSolarProduction']	
		
		#Pull in all info needed by doing lookups on a key.
		key = customerOfInterest
		for field in infoFields:
			lookup(key,info,field,bill)
			
		key = {'utility':bill['utility'],'state':bill['state']}
		for field in nemRulesFields:
			lookup(key,nemRules,field,bill)

		key = {'utility':bill['utility'],'month':bill['month']}
		lookup(key,seasons,'rateSeason',bill)
		
		key = {'utility':bill['utility'],'rateSeason':bill['rateSeason'],'rateSchedule':bill['rateSchedule']}
		for field in allRatesFields:
			dateRangeLookup(key,rates,bill['midpointDate'],'realStart','realEnd',field,bill)
		#print(bill)	
		
		#The distribution rates need to be lists in order to do rateCalcs, so make them into list.
		bill['cumulativeCutoffsList'] = makeListFromDictionaryEntries(bill,cumulativeCutoffFields)
		bill['nonCumulativeCutoffsList'] = makeListFromDictionaryEntries(bill,nonCumulativeCutoffFields)
		bill['tierPriceList'] = makeListFromDictionaryEntries(bill,tierPriceFields)

	#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
	#STEP 2: Now that we have the info we need, do billcalcs
	#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
	#Pre solar bill has 1 component, utility bill.
	#Post-solar bill is the sum of two components: trued-up utility bills, and PPA bills

	#Sort bills in ascending order by date
	customerBills.sort(key=operator.itemgetter('billStart'))



	#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
	#Pre-solar bills
	#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

	#Get pre-solar kWh and utility bill.
	cumulativePreSolarKwh = 0
	cumulativePreSolarBill = 0
	for bill in customerBills:
		preSolarBillDeterminants  = (bill['preSolarGrossKwh'],bill['cumulativeCutoffsList'],bill['lengthInDays'],bill['allowancePerDay'],bill['nonCumulativeCutoffsList'],bill['tierPriceList'],bill['genRate'],bill['fixedCharges'])	
		preSolarBill = calculateStandardUtilityBill(*preSolarBillDeterminants)	
		#print('Pre solar bill is: ',preSolarBill)
		cumulativePreSolarBill = preSolarBill + cumulativePreSolarBill #DO I NEED THIS? IS IT SIGNIFICANT?
		cumulativePreSolarKwh = bill['preSolarGrossKwh'] + cumulativePreSolarKwh

	#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
	#Post-solar bills
	#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx	
	
	#Get post-solar utility bills from actual PDF's. This a ground truth to test the results.
	totalCurrentCharges = 0
	totalNscDisbursed = 0
	totalNemChargesBeforeTaxes = 0
	
	for bill in customerBills:
		totalCurrentCharges           = totalCurrentCharges        + bill['currentCharges']
		totalNscDisbursed             = totalNscDisbursed          + bill['nscDisbursed']
		totalNemChargesBeforeTaxes    = totalNemChargesBeforeTaxes + bill['nemChargesBeforeTaxes']
			
		actualPostSolarUtilityBill = max(totalNemChargesBeforeTaxes,totalCurrentCharges) + totalNscDisbursed
	

	#Get CALCULATED post-solar kWh and utility bill (does not include PPA)
	cumulativePostSolarKwh = 0
	cumulativePostSolarUtilityBill = 0
	cumulativePostSolarCurrentCharges = 0

	for bill in customerBills:

		#Make a billingDeterminants tuple for the four bill types: preSolar, standardPostSolar, exportBill, and fixedChargeOnly
		standardPostSolarBillDeterminants = (bill['postSolarNetKwh'],bill['cumulativeCutoffsList'],bill['lengthInDays'],bill['allowancePerDay'],bill['nonCumulativeCutoffsList'],bill['tierPriceList'],bill['genRate'],bill['fixedCharges'])
		specialExportBillDeterminants = (bill['postSolarNetKwh'],bill['exportCredit'],bill['lengthInDays'],bill['fixedCharges'])
		fixedChargeOnlyBillDeterminants = (bill['lengthInDays'],bill['fixedCharges'])
		
		#Calculate cumulative post-solar kWh AND dollars. Used for both true-up purposes and in bill calcs below 
		cumulativePostSolarKwh = bill['postSolarNetKwh'] + cumulativePostSolarKwh
		cumulativePostSolarCurrentCharges = bill['currentCharges'] + cumulativePostSolarCurrentCharges
		
		#Calculate bill
		if bill['billOnStandardRateInAllMonths'] == 1:
			postSolarUtilityBill = calculateStandardUtilityBill(*standardPostSolarBillDeterminants)
			print('Standard Bill is: ',postSolarUtilityBill)
			
		elif bill['specialExportRate'] == 1 and bill['postSolarNetKwh'] <=0:
			postSolarUtilityBill = calculateSpecialExportUtilityBill(*specialExportBillDeterminants)
			print('Special Export Bill is: ',postSolarUtilityBill)
			
		elif bill['specialExportRate'] == 1 and bill['postSolarNetKwh'] >0:
			postSolarUtilityBill = calculateStandardUtilityBill(*standardPostSolarBillDeterminants)
			print('Standard Bill is: ',postSolarUtilityBill)
			
		elif bill['fixedChargeForNegativeKwh'] == 1 and bill['postSolarNetKwh'] >0 and cumulativePostSolarKwh>0:
			postSolarUtilityBill = calculateStandardUtilityBill(*standardPostSolarBillDeterminants)
			print('Standard Bill is: ',postSolarUtilityBill)
			
		elif bill['fixedChargeForNegativeKwh'] == 1 and (bill['postSolarNetKwh'] <=0 or cumulativePostSolarKwh<=0):
			postSolarUtilityBill = calculateFixedChargeOnlyUtilityBill(*fixedChargeOnlyBillDeterminants)
			print('Fixed Charge Only Bill is: ',postSolarUtilityBill)
		else:
			#print('ERROR!')
			break
		
		#Calculate cumulative post-solar bill
		cumulativePostSolarUtilityBill = postSolarUtilityBill + cumulativePostSolarUtilityBill 


	#True-up the bills just calculated above. This is the FINAL amount owed to the utility for usage over the past year.
	#Grab the information from the first bill; it doesn't matter, it's arbitrary, it's the same for every bill.
	#print(customerBills[0]['nscDeterminant'],customerBills[0]['nscRate'])
	#print((cumulativePostSolarKwh,cumulativePostSolarUtilityBill,customerBills[0]['nscDeterminant'],customerBills[0]['nscRate']))
	#print(type(cumulativePostSolarKwh))


	postSolarTrueUpBill = calculatePostSolarTrueUpBill(cumulativePostSolarKwh,cumulativePostSolarUtilityBill,customerBills[0]['nscDeterminant'],customerBills[0]['nscRate'])

		
	#Get PPA bill.
	cumulativePostSolarPpaBill = 0
	for bill in customerBills:
		solarPpaBill = calculateSolarPpaBill(bill['ppa'],bill['postSolarSolarProduction'])
		cumulativePostSolarPpaBill = solarPpaBill + cumulativePostSolarPpaBill 


	#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
	#Perform savings calcs.
	#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx	
	totalPostSolarBill = postSolarTrueUpBill + cumulativePostSolarPpaBill
	totalPreSolarBill = cumulativePreSolarBill
	savings = totalPreSolarBill - totalPostSolarBill
	residual = postSolarTrueUpBill - actualPostSolarUtilityBill #Check WattzOn results versus the utility bill
	
	#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
	#Calculations complete; add to results.
	#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
	results = {'customer': bill['customer'],'cumulativePreSolarKwh' : cumulativePreSolarKwh ,'cumulativePostSolarKwh' : cumulativePostSolarKwh ,'totalPreSolarBill' : totalPreSolarBill ,'postSolarTrueUpBill' : postSolarTrueUpBill ,'cumulativePostSolarPpaBill' : cumulativePostSolarPpaBill ,'totalPostSolarBill' : totalPostSolarBill ,'actualPostSolarUtilityBill' : actualPostSolarUtilityBill ,'residual' : residual ,'savings' : savings} 
	allResults.append(results)
	

#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
#Write results to CSV file
#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx	
	
keysToWrite = ['customer','cumulativePreSolarKwh','cumulativePostSolarKwh','totalPreSolarBill','postSolarTrueUpBill','cumulativePostSolarPpaBill','totalPostSolarBill','actualPostSolarUtilityBill','residual','savings']

with open('billCalculationOutputs.csv', 'w', newline ='') as output_file:
	dict_writer = csv.DictWriter(output_file, keysToWrite)
	dict_writer.writeheader()
	dict_writer.writerows(allResults)


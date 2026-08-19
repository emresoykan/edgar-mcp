import unittest

from form_parsers import parse_13f_table, parse_form4

FORM4 = """<?xml version="1.0"?>
<ownershipDocument>
  <periodOfReport>2024-01-15</periodOfReport>
  <issuer>
    <issuerCik>0000320193</issuerCik>
    <issuerName>Apple Inc.</issuerName>
    <issuerTradingSymbol>AAPL</issuerTradingSymbol>
  </issuer>
  <reportingOwner>
    <reportingOwnerId>
      <rptOwnerCik>0001214156</rptOwnerCik>
      <rptOwnerName>COOK TIMOTHY D</rptOwnerName>
    </reportingOwnerId>
    <reportingOwnerRelationship>
      <isDirector>1</isDirector>
      <isOfficer>1</isOfficer>
      <officerTitle>Chief Executive Officer</officerTitle>
    </reportingOwnerRelationship>
  </reportingOwner>
  <nonDerivativeTable>
    <nonDerivativeTransaction>
      <securityTitle><value>Common Stock</value></securityTitle>
      <transactionDate><value>2024-01-15</value></transactionDate>
      <transactionCoding>
        <transactionFormType>4</transactionFormType>
        <transactionCode>S</transactionCode>
      </transactionCoding>
      <transactionAmounts>
        <transactionShares><value>1000</value></transactionShares>
        <transactionPricePerShare><value>185.50</value></transactionPricePerShare>
        <transactionAcquiredDisposedCode><value>D</value></transactionAcquiredDisposedCode>
      </transactionAmounts>
      <postTransactionAmounts>
        <sharesOwnedFollowingTransaction><value>3000000</value></sharesOwnedFollowingTransaction>
      </postTransactionAmounts>
    </nonDerivativeTransaction>
  </nonDerivativeTable>
</ownershipDocument>
"""

FORM13F = """<?xml version="1.0"?>
<informationTable xmlns="http://www.sec.gov/edgar/document/thirteenf/informationtable">
  <infoTable>
    <nameOfIssuer>APPLE INC</nameOfIssuer>
    <titleOfClass>COM</titleOfClass>
    <cusip>037833100</cusip>
    <value>123456</value>
    <shrsOrPrnAmt>
      <sshPrnamt>1000000</sshPrnamt>
      <sshPrnamtType>SH</sshPrnamtType>
    </shrsOrPrnAmt>
    <investmentDiscretion>SOLE</investmentDiscretion>
    <votingAuthority>
      <Sole>1000000</Sole>
      <Shared>0</Shared>
      <None>0</None>
    </votingAuthority>
  </infoTable>
</informationTable>
"""


class Form4Tests(unittest.TestCase):
    def test_parses_sale(self):
        doc = parse_form4(FORM4)
        self.assertEqual(doc["issuer"]["ticker"], "AAPL")
        self.assertEqual(doc["reporting_owner"]["name"], "COOK TIMOTHY D")
        self.assertEqual(len(doc["transactions"]), 1)
        tx = doc["transactions"][0]
        self.assertEqual(tx["code"], "S")
        self.assertEqual(tx["shares"], 1000)
        self.assertEqual(tx["price"], 185.5)
        self.assertEqual(tx["acquired_or_disposed"], "D")


class Form13FTests(unittest.TestCase):
    def test_parses_namespaced_table(self):
        rows = parse_13f_table(FORM13F)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["cusip"], "037833100")
        self.assertEqual(rows[0]["value_thousands_usd"], 123456)
        self.assertEqual(rows[0]["shares"], 1000000)


if __name__ == "__main__":
    unittest.main()

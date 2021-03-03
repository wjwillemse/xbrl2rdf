
XBRL_LINKBASE = 1
XBRL_SCHEMA = 0

XLINK_TYPE = '{http://www.w3.org/1999/xlink}type'
XLINK_LABEL = '{http://www.w3.org/1999/xlink}label'
XLINK_HREF = '{http://www.w3.org/1999/xlink}href'
XLINK_ID = '{http://www.w3.org/1999/xlink}id'
XLINK_BASE = '{http://www.w3.org/1999/xlink}base'
XLINK_FROM = '{http://www.w3.org/1999/xlink}from'
XLINK_TO = '{http://www.w3.org/1999/xlink}to'
XLINK_ARCROLE = '{http://www.w3.org/1999/xlink}arcrole'
XLINK_ROLE = '{http://www.w3.org/1999/xlink}role'
XLINK_TITLE = '{http://www.w3.org/1999/xlink}title'

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

SUBSTITUTIONGROUP = 'substitutionGroup'
NILLABLE = 'nillable'
ABSTRACT = 'abstract'
MERGE = 'merge'
NILS = 'nils'
STRICT = 'strict'
IMPLICITFILTERING = 'implicitFiltering'
MATCHES = 'matches'
MATCHANY = 'matchAny'
BALANCE = 'balance'
COVER = 'cover'
AXIS = 'axis'
COMPLEMENT = 'complement'
NAME = 'name'
USE = 'use'
PRIORITY = 'priority'
ORDER = 'order'
WEIGHT = 'weight'
AS = 'as'
ID = 'id'

OUTPUT = 'output'
FALLBACKVALUE = 'fallbackValue'
BINDASSEQUENCE = 'bindAsSequence'
ASPECTMODEL = 'aspectModel'
TEST = 'test'
PARENTCHILDORDER = 'parentChildOrder'
SELECT = 'select'
VARIABLE = 'variable'
DIMENSION = 'dimension'
SCHEME = 'scheme'

XBRLI_PERIODTYPE = '{http://www.xbrl.org/2003/instance}periodType'
MODEL_CREATIONDATE = '{http://www.eurofiling.info/xbrl/ext/model}creationDate'
MODEL_TODATE = '{http://www.eurofiling.info/xbrl/ext/model}toDate'
MODEL_FROMDATE = '{http://www.eurofiling.info/xbrl/ext/model}fromDate'
MODEL_MODIFICATIONDATE = '{http://www.eurofiling.info/xbrl/ext/model}modificationDate'
MODEL_DOMAIN = '{http://www.eurofiling.info/xbrl/ext/model}domain'
MODEL_HIERARCHY = '{http://www.eurofiling.info/xbrl/ext/model}hierarchy'
MODEL_ISDEFAULTMEMBER = '{http://www.eurofiling.info/xbrl/ext/model}isDefaultMember'

ENUM_DOMAIN = '{http://xbrl.org/2014/extensible-enumerations}domain'
ENUM_LINKROLE = '{http://xbrl.org/2014/extensible-enumerations}linkrole'

XBRLDT_CONTEXTELEMENT = '{http://xbrl.org/2005/xbrldt}contextElement'
XBRLDT_TARGETROLE = '{http://xbrl.org/2005/xbrldt}targetRole'
XBRLDT_CLOSED = '{http://xbrl.org/2005/xbrldt}closed'
XBRLDT_USABLE = '{http://xbrl.org/2005/xbrldt}usable'
XBRLDT_TYPEDDOMAINREF = '{http://xbrl.org/2005/xbrldt}typedDomainRef'

predicates = {XBRLI_PERIODTYPE:   'xbrli:periodType',
              MODEL_CREATIONDATE: 'model:creationDate',
              MODEL_TODATE:       'model:toDate',
              MODEL_FROMDATE:     'model:fromDate',
              MODEL_MODIFICATIONDATE: 'model:modificationDate',
              MODEL_DOMAIN:       'model:domain',
              MODEL_HIERARCHY:    'model:hierarchy',
              MODEL_ISDEFAULTMEMBER: 'model:isDefaultMember',
              XBRLDT_TYPEDDOMAINREF: 'xbrldt:typedDomainRef',
              XBRLDT_TARGETROLE: 'xbrldt:targetRole',
              ENUM_DOMAIN: 'enum:domain',
              ENUM_LINKROLE: 'enum:linkrole',
              SUBSTITUTIONGROUP: 'xbrli:substitutionGroup',
              NILLABLE: 'xbrli:nillable',
              ABSTRACT: 'xbrli:abstract',
              BALANCE: 'xbrli:balance',
              MERGE: 'xbrli:merge',
              NILS: 'xbrli:nils',
              STRICT: 'xbrli:strict',
              IMPLICITFILTERING: 'xbrli:implicitFiltering',
              MATCHES: 'xbrli:matches',
              MATCHANY: 'xbrli:matchAny',
              XBRLDT_CONTEXTELEMENT: 'xbrldt:contextElement',
              XBRLDT_CLOSED: 'xbrldt:closed',
              XBRLDT_USABLE: 'xbrldt:usable',
              COVER: 'xl:cover',
              AXIS: 'xl:axis',
              COMPLEMENT: 'xl:complement',
              NAME: 'xl:name',
              USE: 'xl:use',
              PRIORITY: 'xl:priority',
              ORDER: 'xl:order',
              WEIGHT: 'xl:weight',
              AS: 'xl:as',
              OUTPUT: 'xl:output',
              FALLBACKVALUE: 'xl:fallbackValue',
              BINDASSEQUENCE: 'xl:bindAsSequence',
              ASPECTMODEL: 'xl:aspectModel',
              TEST: 'xl:test',
              PARENTCHILDORDER: 'xl:parentChildOrder',
              SELECT: 'xl:select',
              VARIABLE: 'xl:variable',
              DIMENSION: 'xl:dimension',
              SCHEME: 'xl:scheme',

              XML_LANG: 'rdf:lang',
              XLINK_ROLE: 'xlink:role'
}

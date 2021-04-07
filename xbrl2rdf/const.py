
XBRL_SCHEMA: int = 0
XBRL_LINKBASE: int = 1

XLINK_TYPE: str = '{http://www.w3.org/1999/xlink}type'
XLINK_LABEL: str = '{http://www.w3.org/1999/xlink}label'
XLINK_HREF: str = '{http://www.w3.org/1999/xlink}href'
XLINK_ID: str = '{http://www.w3.org/1999/xlink}id'
XLINK_BASE: str = '{http://www.w3.org/1999/xlink}base'
XLINK_FROM: str = '{http://www.w3.org/1999/xlink}from'
XLINK_TO: str = '{http://www.w3.org/1999/xlink}to'
XLINK_ARCROLE: str = '{http://www.w3.org/1999/xlink}arcrole'
XLINK_ROLE: str = '{http://www.w3.org/1999/xlink}role'
XLINK_TITLE: str = '{http://www.w3.org/1999/xlink}title'

XML_LANG: str = "{http://www.w3.org/XML/1998/namespace}lang"

SUBSTITUTIONGROUP: str = 'substitutionGroup'
NILLABLE = 'nillable'
ABSTRACT: str = 'abstract'
MERGE: str = 'merge'
NILS: str = 'nils'
STRICT: str = 'strict'
IMPLICITFILTERING: str = 'implicitFiltering'
MATCHES: str = 'matches'
MATCHANY: str = 'matchAny'
BALANCE: str = 'balance'
COVER: str = 'cover'
AXIS: str = 'axis'
PREFERRED_LABEL: str = 'preferredLabel'
COMPLEMENT: str = 'complement'
NAME: str = 'name'
USE: str = 'use'
PRIORITY: str = 'priority'
ORDER: str = 'order'
WEIGHT: str = 'weight'
AS: str = 'as'
ID: str = 'id'

OUTPUT: str = 'output'
FALLBACKVALUE: str = 'fallbackValue'
BINDASSEQUENCE: str = 'bindAsSequence'
ASPECTMODEL: str = 'aspectModel'
TEST: str = 'test'
PARENTCHILDORDER: str = 'parentChildOrder'
SELECT: str = 'select'
VARIABLE: str = 'variable'
DIMENSION: str = 'dimension'
SCHEME: str = 'scheme'

XBRLI_PERIODTYPE: str = '{http://www.xbrl.org/2003/instance}periodType'
XBRLI_BALANCE: str = '{http://www.xbrl.org/2003/instance}balance'
MODEL_CREATIONDATE: str = '{http://www.eurofiling.info/xbrl/ext/model}creationDate'
MODEL_TODATE: str = '{http://www.eurofiling.info/xbrl/ext/model}toDate'
MODEL_FROMDATE: str = '{http://www.eurofiling.info/xbrl/ext/model}fromDate'
MODEL_MODIFICATIONDATE: str = '{http://www.eurofiling.info/xbrl/ext/model}modificationDate'
MODEL_DOMAIN: str = '{http://www.eurofiling.info/xbrl/ext/model}domain'
MODEL_HIERARCHY: str = '{http://www.eurofiling.info/xbrl/ext/model}hierarchy'
MODEL_ISDEFAULTMEMBER: str = '{http://www.eurofiling.info/xbrl/ext/model}isDefaultMember'

ENUM_DOMAIN: str = '{http://xbrl.org/2014/extensible-enumerations}domain'
ENUM_LINKROLE: str = '{http://xbrl.org/2014/extensible-enumerations}linkrole'

XBRLDT_CONTEXTELEMENT: str = '{http://xbrl.org/2005/xbrldt}contextElement'
XBRLDT_TARGETROLE: str = '{http://xbrl.org/2005/xbrldt}targetRole'
XBRLDT_CLOSED: str = '{http://xbrl.org/2005/xbrldt}closed'
XBRLDT_USABLE: str = '{http://xbrl.org/2005/xbrldt}usable'
XBRLDT_TYPEDDOMAINREF: str = '{http://xbrl.org/2005/xbrldt}typedDomainRef'

predicates: dict = {XBRLI_PERIODTYPE:   'xbrli:periodType',
              XBRLI_BALANCE:      'xbrli:balance',
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
              PREFERRED_LABEL: 'xl:preferredLabel',
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
              XLINK_ROLE: 'xlink:role'}

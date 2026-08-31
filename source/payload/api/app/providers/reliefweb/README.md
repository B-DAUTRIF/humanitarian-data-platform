# ReliefWeb provider package

This package is the target V7 provider architecture. `reliefweb_v2.py` remains a compatibility contract during migration. All new execution paths must converge on `ReliefWebService`; the legacy semantic `/reports` executor is explicitly transitional and must be removed only after regression coverage proves parity.

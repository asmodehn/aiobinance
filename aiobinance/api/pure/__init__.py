"""
Functional Design for python API:

The access structure of concepts is hierarchical:

Exchange: only ONE
    Markets:  many (ETHEUR, BTCETH, etc.)
        price  one, changing over time
        trades  many, changing overtime and aggregating
Account: only ONE
    Assets: many (ETH, EUR, BTC, etc.)
        ledger  one, changing overtime (from trades !)
        positions many, changing overtime and aggregating

Concepts are represented by a class, often delegating to a Model for data manipulation.
These class are interwoven together to form a (hopefully) consistent whole.

The "*View" concepts are dynamic and provide functionality to run "out of control flow", ie. in the background.

                                         |
                             Public      |    Private
                                         |

                         +----------+         +---------+
                         | Exchange |<--------| Account |
                         +----------+         +---------+
                              |                    |
                              |                    |
                              v                    v
                        +----------+          +---------+
      +---------------- |  Market  |<---------|  Asset  |-------------------+
      |                 +----------+          +---------+                   |
      |                    +                         +                      |
      |                    |                         |                      |
+-----v------+             |                         |              +-------v------+
|  OHLCView  |             |                         |              | PostionsView |
+------------+             |                         |              +--------------+
                           |                         |
                           v                         v
                   +--------------+          +--------------+
                   |  TradesView  <---------+|  LedgerView  |
                   +--------------+          +--------------+


Ref : https://textik.com/#80671cf6c2d3bb46

"""

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

                                  +----------+
                          +-------| Exchange |------+     Only one -> should be just data (no class needed) ?
                          |       +----------+      |     data, but mostly constant in runtime (explicit updates)
                          |                         |
                          v                         v
                       +----------+          +---------+
      +----------------|  Market  |          | Account |----------------------+    many (per symbol & per subaccount)
      |                +----------+          +---------+                      |    -> class but mostly constant in runtime (explicit updates)
      |                       +   |->OrderViews<-|  +                         |    -> cached as data in python modules.
      |                       |                     |                         |
      |                       v                     v                         v
+-----v------+         +--------------+        +--------------+        +--------------+
|  OHLCView  |         |  TradesView  |<-------+  LedgerView  |        | PostionsView |    many x many, encapsulating time-related changes...
+------------+         +--------------+        +--------------+        +--------------+

Ref : https://textik.com/#80671cf6c2d3bb46

"""

"""
Functional Design for python API:

The access structure of concepts is hierarchical:

Exchange:
    Markets:  many (ETHEUR, BTCETH, etc.)
        price  one, changing over time
        trades  many, changing overtime and aggregating
    Account:  only ONE
        assets  many, amount changing overtime
        positions  many, changing over time and aggregating

Concepts are represented by a class, often delegating to a Model for data manipulation.
These class are interwoven together to form a (hopefully) consistent whole.

"""

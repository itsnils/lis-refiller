# Created by bludi at 26-Oct-18
Feature: Automated humidity column refiller
  in order to allow long-term unattended operation
  a weighing ring shall measure the weight of the column
  and a pump shall refill it

  Scenario: Weight is smaller than zeroed weight
    Given pump is idle
    And weight is in the plausible range
    Then pump a defined volume

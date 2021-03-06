#!/usr/bin/env python
#coding: utf-8

import sys
import time
import rospy
import json
from std_msgs.msg import String, Empty, Float64
from mutualModelling.agent2 import Agent

# this node udate models of agents (by the robot) and publishes the choice of action by the robot:
#-------------------------------------------------------------------------------------------------
pub_robot_action = rospy.Publisher('robot_action_topic', String, queue_size=1)

# create a mutual modeller agent "robot" that also model an agent "human" in cowriter:
#-------------------------------------------------------------------------------------
ROBOT_NAME = "Mimi"
HUMAN_NAME = "Child"
ALL_NAMES = [ROBOT_NAME, HUMAN_NAME]
robot_percepts = ["child_progress","reward","punish","justified_reward","justified_punish","justified_new_word","with_me"]
robot_actions = ["converges","diverges","exaggerates","looks_tablet","looks_child_head","looks_out","looks_experimentator","looks_selection_tablet","points_tablet"]
robot_rewards = [["justified_reward",1.,1.],["justified_punish",1.,1],["with_me",1.,1.],["with_me",-1.,-1.],["child_progress",1.,1.],["justified_new_word",1.,1.]]
#robot_instincts = [[HUMAN_NAME+"_looks_robot_head",1.,"looks_child_head"],[HUMAN_NAME+"_looks_robot_head",1.,"looks_tablet"], [HUMAN_NAME+"_looks_tablet",1.,"looks_child_head"],[HUMAN_NAME+"_looks_tablet",1.,"looks_tablet"], [HUMAN_NAME+"_looks_noise",1.,"looks_child_head"],[HUMAN_NAME+"_looks_noise",1.,"mimics"], [HUMAN_NAME+"_looks_selection_tablet",1.,"looks_selection_tablet"], [HUMAN_NAME+"_looks_experimentator",1.,"looks_experimentator"]]
#robot = Agent(ROBOT_NAME,ALL_NAMES,robot_percepts,robot_actions,robot_rewards,robot_instincts)
robot = Agent(ROBOT_NAME,ALL_NAMES,robot_percepts,robot_actions,robot_rewards)

# the point of attention of the human is used to define what action of the robot is observed by the child:
#---------------------------------------------------------------------------------------------------------
objects = {"experimentator","selection_tablet","tablet","robot_head","out"}
human_attention = ""

# what the human can perceive about robot actions given his point of attention:
visible_for_human_from = {"tablet":["converges","diverges"], "robot_head":["looks_tablet","looks_child_head","looks_out","points_tablet","looks_experimentator"]}

# what the robot is expected to perceive about human action given robot's attention:
# (the robot is not expected (by the child) to differentiate justified/unjustified behavior of the child)
visible_for_robot_from = {"tablet":["punishes","rewards","sends_demo"],"selection_tablet":["sends_new_word"], "child_head":["looks_tablet","looks_robot_head","looks_out","looks_experimentator"]}

# when an agent do/observe something the mutual models (by the robot) are updated:
#---------------------------------------------------------------------------------
models_percepts = {}
models_actions = {}
human_target = "_"
robot_target = "_"
last_info = ""

def onChangeRobotTarget(msg):
    global robot_target
    robot_target = str(msg.data)

def onChangeHumanTarget(msg):
    global human_target
    human_target = str(msg.data)

def onChangeHumanWMN(msg):
    global last_info
    delta_wmn = msg.data
    if last_info!=str(delta_wmn):
        models_percepts.setdefault(ROBOT_NAME,[]).append(("with_me",delta_wmn))
        makeDecision()
        last_info = str(delta_wmn)

def onRobotAction(msg):
    global models_actions
    global models_percepts
    global last_info
    action = str(msg.data)
    if last_info!=action:
        if human_target in visible_for_human_from:
            if action in visible_for_human_from[human_target]:
                models_actions[HUMAN_NAME+':'+ROBOT_NAME] = action
                models_percepts.setdefault(HUMAN_NAME,[]).append((ROBOT_NAME+"_"+action,1.))
                rospy.loginfo(ROBOT_NAME+"_"+action)
                rospy.loginfo(".........................................")
        makeDecision()
        last_info=action

def onHumanAction(msg):
    global models_actions
    global models_percepts
    global last_info
    action = str(msg.data)
    if last_info!=action:
        models_actions[HUMAN_NAME] = action
        models_percepts.setdefault(ROBOT_NAME,[]).append((HUMAN_NAME+'_'+action,1.))
        rospy.loginfo(HUMAN_NAME+'_'+action)
        rospy.loginfo("////////////////////////////////////////")
        if robot_target in visible_for_robot_from:
            if action in visible_for_robot_from[robot_target]:
                models_percepts.setdefault(HUMAN_NAME+':'+ROBOT_NAME,[]).append((HUMAN_NAME+"_"+action,1.))
        makeDecision()
        last_info=action

def makeDecision():
    global robot
    global models_actions
    global models_percepts
    new_robot_action = None
    if models_actions:
        new_robot_action = robot.update_models(None,models_percepts,models_actions)
        rospy.loginfo(models_percepts)
        rospy.loginfo(models_actions)
        #rospy.loginfo(test)
        rospy.loginfo("----------------------------------------")
    if new_robot_action:
        msg = String()
        msg.data = new_robot_action
        pub_robot_action.publish(msg)
    models_percepts = {}
    models_actions = {}
    rospy.sleep(1.0)

# TODO:
"""
def onRobotObs(msg):

def onHumanObs(msg):
"""

if __name__=='__main__':

    rospy.init_node("cowriter_mutual_modelling")

    while(True):
        rospy.Subscriber('robot_action_topic', String, onRobotAction )
        rospy.Subscriber('human_action_topic', String, onHumanAction)
        rospy.Subscriber('robot_target_topic', String, onChangeRobotTarget)
        rospy.Subscriber('human_target_topic', String, onChangeHumanTarget)
        rospy.Subscriber('human_wmn_topic', Float64, onChangeHumanWMN)
        #rospy.Subscriber('robot_obs_topic', String, onRobotObs)
        #rospy.Subscriber('human_obs_topic', String, onHumanObs)


        rospy.sleep(1.0)

    rospy.spin()

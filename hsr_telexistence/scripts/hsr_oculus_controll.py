#!/usr/bin/env python3
# coding: utf-8
import rospy
import trajectory_msgs.msg
import geometry_msgs.msg
from oculus_telexistence.msg import *
import actionlib
import controller_manager_msgs.srv
import tmc_control_msgs.msg
from std_msgs.msg import Bool
from sensor_msgs.msg import JointState
class OCULUS_control:
    def __init__(self):
        self.sub_joy = rospy.Subscriber("oculus/button", OculusButton, self.subscribe_joy, queue_size=10)
        self.sub_joi = rospy.Subscriber("hsrb/joint_states", JointState, self.subscribe_joi, queue_size=10)
        self.pub_wheel_control = rospy.Publisher('hsrb/command_velocity',geometry_msgs.msg.Twist,queue_size=10)
        self.pub_gripper = rospy.Publisher(
            '/hsrb/gripper_controller/command',
            trajectory_msgs.msg.JointTrajectory, queue_size=10)
        self.hand = rospy.Publisher("main_hand", Bool, queue_size=10)
        self.feedback = rospy.Publisher("hsr_feedback", Bool, queue_size=10)
        self.hand_state_new = 0.0
        self.hand_msg = Bool()
        self.feedback_msg = Bool()
        #rate
        self.rate = rospy.Rate(10)
        #subscriberのメッセージを受け取る変数
        self.joy_button = [0] * 19
        self.left_joystick_lr = 0
        self.left_joystick_ud = 0
        self.right_joystick_lr = 0
        self.right_joystick_ud = 0
        self.magnifications = 0.3
        self.joint_pub_time = 0.001
        self.hand_state = 1.0
        self.is_left_hand = rospy.get_param("hand")
        self.hand_msg.data = self.is_left_hand
        self.hand_motor_state = 0
        self.new_hand_motor_state = 0



    def subscribe_joy(self, msg):
        self.joy_button[0] = msg.ButtonX.data
        self.joy_button[1] = msg.ButtonA.data
        self.joy_button[2] = msg.ButtonY.data
        self.joy_button[3] = msg.ButtonB.data
        self.joy_button[4] = msg.MenuButton.data
        self.joy_button[5] = msg.ThumbstickL.data
        self.joy_button[6] = msg.ThumbstickR.data
        self.joy_button[7] = msg.ThumbstickLU.data
        self.joy_button[8] = msg.ThumbstickRU.data
        self.joy_button[9] = msg.ThumbstickLR.data
        self.joy_button[10] = msg.ThumbstickRR.data
        self.joy_button[11] = msg.ThumbstickLD.data
        self.joy_button[12] = msg.ThumbstickRD.data
        self.joy_button[13] = msg.ThumbstickLL.data
        self.joy_button[14] = msg.ThumbstickRL.data
        self.joy_button[15] = msg.TriggerL.data
        self.joy_button[16] = msg.TriggerR.data
        self.joy_button[17] = msg.GripButtonL.data
        self.joy_button[18] = msg.GripButtonR.data
        self.left_joystick_lr = msg.ThumbstickLA.x * self.magnifications
        self.left_joystick_ud = msg.ThumbstickLA.y * self.magnifications
        self.right_joystick_lr = msg.ThumbstickRA.x * self.magnifications
        self.right_joystick_ud = msg.ThumbstickRA.y * self.magnifications
    
    def subscribe_joi(self, msg):
        self.hand_motor_state = msg.position[7]



    def check_publishers_connection(self, publisher):
        loop_rate_to_check_connection = rospy.Rate(1)
        while (publisher.get_num_connections() == 0 and not rospy.is_shutdown()):
            try:
                loop_rate_to_check_connection.sleep()
            except rospy.ROSInterruptException:
                pass
 
    
    def move_wheel(self, linear_x, angular):
        twist = geometry_msgs.msg.Twist()
        if self.is_left_hand:
            if self.joy_button[16]:
                twist.angular.z = -self.right_joystick_lr * angular
                twist.linear.x = self.right_joystick_ud * linear_x
            if self.joy_button[18]:
                if self.joy_button[1]:
                    self.hand_state += 0.2
                else:
                    self.hand_state -= 0.2
        else:
            if self.joy_button[15]:
                twist.angular.z = -self.left_joystick_lr * angular
                twist.linear.x = self.left_joystick_ud * linear_x
            if self.joy_button[17]:
                if self.joy_button[0]:
                    self.hand_state += 0.2
                else:
                    self.hand_state -= 0.2

        if self.hand_state > 1.3:
            self.hand_state = 1.3
        elif self.hand_state < -0.8:
            self.hand_state = -0.8
        if self.hand_state_new != self.hand_state:
            print("The finger is moving")
            self.grasp(self.hand_state)
            self.judge()
        self.check_publishers_connection(self.pub_wheel_control)
        self.pub_wheel_control.publish(twist)
        self.hand_state_new = self.hand_state

    def grasp(self, effort):
        # fill ROS message
        traj = trajectory_msgs.msg.JointTrajectory()
        traj.joint_names = ["hand_motor_joint"]
        p = trajectory_msgs.msg.JointTrajectoryPoint()
        p.positions = [effort]
        p.velocities = [0]
        p.effort = [5.0]
        p.time_from_start = rospy.Duration(0.01)
        traj.points = [p]
        # publish ROS message
        self.pub_gripper.publish(traj)

  
    def judge(self):
        e = self.new_hand_motor_state - self.hand_motor_state
        print(e)
        if self.hand_motor_state < -0.5:
            self.feedback_msg.data = False
        elif e > 0.01 and e < 0.06:
            self.feedback_msg.data = True
            self.feedback.publish(self.feedback_msg)
            rospy.sleep(0.5)
            self.feedback_msg.data = False
            self.feedback.publish(self.feedback_msg)
        else:
            self.feedback_msg.data = False
        self.new_hand_motor_state = self.hand_motor_state




    def pub_joy(self):
        while not rospy.is_shutdown():
            self.move_wheel(5.0, 5.0)
            self.rate.sleep()
            self.hand.publish(self.hand_msg)
            


            


if __name__ == '__main__':
    rospy.init_node('hsr_oculus_control_node')
    jc = OCULUS_control()
    jc.pub_joy()
    rospy.spin()

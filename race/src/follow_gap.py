#!/usr/bin/env python

import rospy
import math
from sensor_msgs.msg import LaserScan
from ackermann_msgs.msg import AckermannDrive

command_pub = rospy.Publisher('/car_1/offboard/command', AckermannDrive, queue_size = 1)

#! only for testing lidar values 
def getRange(data,angle):

    angle_rad = math.radians(angle-90)
    ind = int((angle_rad - data.angle_min) / data.angle_increment)

    print(ind)

    dist = data.ranges[ind]

    return dist

def findLargestGap(rangeList):
    maxSize = 0
    maxStart = None

    currSize = 0
    currStart = None

    for i in range(len(rangeList)):
        if rangeList[i] == 0:
            if currSize > maxSize:
                maxSize = currSize
                maxStart = currStart
            currSize = 0
            currStart = None
        else:
            if currStart == None:
                currStart = i
            currSize += 1

    if currSize > maxSize:
                maxSize = currSize
                maxStart = currStart

    if maxStart != None:
        middle = maxStart + (maxSize-1) //  2
        return middle
    else:
        maxRange = -1
        maxInd = -1
        for i in range(len(rangeList)):
            if rangeList[i] > maxRange:
                maxRange = rangeList[i]
                maxInd = i
        return maxInd

def callback(data):
    global threshold
    global velocity

    halfCarWidth = 0.15

    #* 1.Take the raw array of Lidar samples. Find disparities in the Lidar readings. A disparity is two subsequent points in the
    #* array of distance values that differ by some amount larger than some predefined threshold. Threshold of 0.1m is a good starting
    #* point but try different values.
    ranges = list(data.ranges)

    # neg90 = int((-1.571 - data.angle_min -1.571) / data.angle_increment)
    # pos90 = int((1.571 - data.angle_min - 1.571) / data.angle_increment)
    # zero = int((0 - data.angle_min - 1.571) / data.angle_increment)

    # print()
    # print(ranges[127])
    # print("Left: ", getRange(data, 180))
    # print("Front: ", getRange(data, 90))
    # print("Right: ", getRange(data, 0))


    #TODO NaNs?
    ranges = [4 if math.isnan(x) else x for x in ranges]
    #! remove all above 2 to fix wiggling, all below 1 to make 
    distMax = 5
    distMin = 0.01

    ranges = [x if distMin < x and x < distMax else 0 for x in ranges]

    neg90 = 127 # RIGHT!
    pos90 = 639 # LEFT!
    total = 725

    ranges[:neg90] = [0] * neg90
    ranges[pos90:] = [0] * (total-pos90)

    # print(ranges)
    
    # print("Disparities: ")
    # print("__________Before____________")
    # print("Left: ", ranges[127])
    # print("Front: ", ranges[383])
    # print("Right: ", ranges[639])

    for i in range(len(ranges)-1):
        if abs(ranges[i] - ranges[i+1]) > threshold:
            # print(i)
             
            #* 2. For each pair of points around a disparity, pick the point at the closer distance. Calculate the number of LIDAR samples needed
            #* to cover half the width of the car, plus some tolerance, at this distance.
            if ranges[i] < ranges[i+1] and ranges[i] != 0:
                #! horizontal distance between two ranges = range * sin(angle difference) 
                dist = ranges[i] * math.sin(data.angle_increment)
                numSamples = int(math.ceil(halfCarWidth / dist))
                # print("Dist:", dist)
                # print("NumSamples:", numSamples)

                #* 3. Starting at the more distant of the two points and continuing in the same direction, overwrite the number of samples in the array
                #* with the closer distance. Do not overwrite any points that are already closer!
                for j in range(numSamples):
                    if i+1+j < len(ranges):
                        ranges[i+1+j] = ranges[i]
                        #! zero version
                        # ranges[i+1+j] = 0


            elif ranges[i+1] < ranges[i] and ranges[i+1] != 0:
                #! horizontal distance between two ranges = range * sin(angle difference) 
                dist = ranges[i+1] * math.sin(data.angle_increment)
                numSamples = int(math.ceil(halfCarWidth / dist))
                # print("Dist:", dist)
                # print("NumSamples:", numSamples)

                #* 3 (again). Starting at the more distant of the two points and continuing in the same direction, overwrite the number of samples in the array
                #* with the closer distance. Do not overwrite any points that are already closer!
                for j in range(numSamples):
                    if i-j > -1:
                        ranges[i-j] = ranges[i+1]
                        #! zero version
                        # ranges[i-j] = 0

    #* 4. Search through these filtered distances corresponding to angles between -90 and +90 degrees (to make sure we don't identify
    #* a path behind the car).
    # print("__________After____________")
    # print("Left: ", ranges[127])
    # print("Front: ", ranges[383])
    # print("Right: ", ranges[639])


    maxRange = 0
    maxInd = -1

    # #TODO naive - maybe use idxmax
    for i in range(len(ranges)):
        if ranges[i] > maxRange:
            # print(ranges[i])
            # print(ranges)
            maxRange = ranges[i]
            maxInd = i



# ==========================CLOSEST STRAIGHT============================
    # gaps2 = []
    # max_dist = 0
    # for i in range(neg90, pos90):
    #     if (ranges[i] > max_dist):
    #         max_dist = ranges[i]
    #         maxInd = i
    #         if len(gaps2)<2:
    #             gaps2.append((max_dist, maxInd))
    #         else:
    #             if abs(gaps2[0][0] > max_dist):
    #                 gaps2[0] = (max_dist, maxInd)
    #             else:
    #                 gaps2[1] = (max_dist, maxInd)

    # if gaps2[0][0] > gaps2[1][0]:
    #     maxInd = gaps2[1][1]
    # else:
    #     maxInd = gaps2[0][1]

# ==========================CLOSEST STRAIGHT============================


    # #* 5. Once you find the sample with the farthest distance in this range, calculate the corresponding angle--that's the direction you
    # #* want to target.
    # print(maxInd)
    # print(maxRange)
    # angle = data.angle_min + (maxInd * data.angle_increment)

    #* 6. Here you can be creative and if there are multiple candidate gaps then you can choose the fatherst/deepest gap or the center of
    #* the widest gap. Try what works best
    #TODO
    #! remove all above 2 to fix wiggling, all below 1 to make 
    # distMax = 2
    # distMin = 1

    # ranges = [x if distMin < x and x < distMax else 0 for x in ranges]

    # maxInd = findLargestGap(ranges)
    # maxRange = ranges[maxInd]

    #* 5. Once you find the sample with the farthest distance in this range, calculate the corresponding angle--that's the direction you
    #* want to target.
    print(maxInd)
    print(maxRange)
    angle = data.angle_min + (maxInd * data.angle_increment)

    #* 7. Actuate the car to move towards this goal point by publishing an `AckermannDrive message to the topic as you did for Wall
    #* Following - the same ranges for steering [-100,100] and velocity [0,100] apply.
    command = AckermannDrive()

    angle_deg = math.degrees(angle)

    if angle_deg < -100:
        angle_deg = -100
    elif angle_deg > 100:
        angle_deg = 100


    command.steering_angle = angle_deg

    #* choose speed based on distance
    # speed = velocity + (1 * maxRange)
    speed = velocity
    command.speed = speed
    # print(ranges[263])


    command_pub.publish(command)
    #* 8. We will move the obstacles around during the demo and the car should be able to avoid them.



if __name__ == '__main__':
	print("Follow The Gap started")
    
	threshold = rospy.get_param("/threshold")
	velocity = rospy.get_param("/velocity")


	rospy.init_node('follow_gap',anonymous = True)

	rospy.Subscriber("/car_1/scan", LaserScan, callback)

	rospy.spin()
import cv2
import numpy as np
import glob
import argparse
import os
import struct
from typing import List
import time
from scipy.spatial import ConvexHull
from flask import Flask, Response
import calibrartion_arm_client
#from numba import jit

app = Flask(__name__)

max_calibration_error = 0.06

@app.route('/left')
def video_feed_left():
    return Response(calibrate_camera('left'), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/right')
def video_feed_right():
    return Response(calibrate_camera('right'), mimetype='multipart/x-mixed-replace; boundary=frame')

# change working directory to script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

chessBoard = (8,6)
calibrationFolder = "/home/baseline/BaselineCrossPlatform/Calibration/"
clibFrameNumber = 40


# termination criteria
#CALIB_CB_NORMALIZE_IMAGE | CALIB_CB_ADAPTIVE_THRESH | CALIB_CB_FILTER_QUADS | CALIB_CB_FAST_CHECK
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
objp = np.zeros((chessBoard[0]*chessBoard[1],3), np.float32)
objp[:,:2] = np.mgrid[0:chessBoard[0],0:chessBoard[1]].T.reshape(-1,2)


# Arrays to store object points and image points from all the images.
objpoints = [] # 3d point in real world space
imgpoints = [] # 2d points in image plane.

def gstreamer_pipeline(
    sensor_id=1,
    capture_width=1920,
    capture_height=1080,
    display_width=1920/2,
    display_height=1080/2,
    framerate=60,
    flip_method=0,
):
    return (
        "nvarguscamerasrc sensor-id=%d ! "
        "video/x-raw(memory:NVMM), width=(int)%d, height=(int)%d, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "queue ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
        % (
            sensor_id,
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )


#@jit
def generateUndistortedLookupTable(cameraMatrix, dist, u, v):
    uv_undist = np.zeros((1920 * 1080, 1, 2), dtype=np.float64)
    for y in range(1080):
        for x in range(1920):
            idx = y * 1920 + x
            uv_undist[idx, 0, 0] = x
            uv_undist[idx, 0, 1] = y
    xy = cv2.undistortPoints(uv_undist, cameraMatrix, dist, None, cameraMatrix)

    for x in range(1920):
        for y in range(1080):
            idx = y * 1920 + x
            u[idx] = xy[idx, 0, 0]
            v[idx] = xy[idx, 0, 1]



def saveDoubleArray(pdata: List[float], file_path: str):
    with open(file_path, 'wb') as f:
        for data in pdata:
            f.write(struct.pack('d', data))
    

def save_calibration(side, mtx, dist, w, h, calib_error):
    print( "saving calibration files..")
    #scale matrix to 1920x1080
    mtx[0][0] = mtx[0][0] * 1920 / w
    mtx[1][1] = mtx[1][1] * 1080 / h
    mtx[0][2] = mtx[0][2] * 1920 / w
    mtx[1][2] = mtx[1][2] * 1080 / h

    # if calibration folder does not exist, create it
    if not os.path.exists(calibrationFolder):
        os.makedirs(calibrationFolder)

    # save calibration "intrinsicMatrix_" + side + ".csv"
    np.savetxt(calibrationFolder + "intrinsicMatrix_" + side + ".csv", mtx, delimiter=",", fmt='%.10f', newline='\n')

    # save "distCoeffs_" + side + ".csv"
    np.savetxt(calibrationFolder + "distCoeffs_" + side + ".csv", dist, delimiter=",", fmt='%.10f', newline='\n')

    s = 1920 * 1080
    ru = [0.0] * s
    rv = [0.0] * s

    print( "generating undistorted lookup tables..")
    generateUndistortedLookupTable(mtx, dist, ru, rv)

    print( "saving undistorted lookup tables..")
    saveDoubleArray(ru, calibrationFolder + "u_undist_lookuptable_" + side + ".dat")
    saveDoubleArray(rv, calibrationFolder + "v_undist_lookuptable_" + side + ".dat")

    print("calibration files saved")

    # restore matrix
    mtx[0][0] = mtx[0][0] * w / 1920
    mtx[1][1] = mtx[1][1] * h / 1080
    mtx[0][2] = mtx[0][2] * w / 1920
    mtx[1][2] = mtx[1][2] * h / 1080

    # save calib_error
    np.savetxt(calibrationFolder + "calib_error_" + side + ".log", [calib_error], delimiter=",", fmt='%.10f', newline='\n')

    


def calibrate_camera(side):
    count = 1
    corners2 = None
    cornersCount = 0

    donecalibration = False
    calib_error = 100
    w = 0
    h = 0
    # sudo systemctl restart nvargus-daemon
    quit = 0
    minImages = 40
    
    print("Calibrating camera lens " + side + " ...")
    print("Press 'q' to quit")
    print(" ************************************************************** ")
    sensor_id=0 if side == "left" else 1
    print(gstreamer_pipeline(sensor_id))
    found = False
    cover = 0
    hull = None
    lastCorners = None
    video_capture = cv2.VideoCapture(gstreamer_pipeline(sensor_id), cv2.CAP_GSTREAMER)
    if video_capture.isOpened():
        try:
            while True:

                if cover >= 75 and cornersCount > 39 and not donecalibration:    
                    # calibratre camera
                    print ("Calibrating camera")

                    # write calibrating oc the center of frame in red
                    h,  w = frame.shape[:2]
                    cv2.putText(frame, "Calibrating please wait...(" + str(cornersCount) + ")", (10, int(h/2)), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3, cv2.LINE_AA)
                    ret, buffer = cv2.imencode('.jpg', frame)
                    bframe = buffer.tobytes()
                    yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + bframe + b'\r\n')
                    yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + bframe + b'\r\n')
                    yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + bframe + b'\r\n')
                    
                    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)
                    print ("h: " + str(h) + " w: " + str(w) + " \nmtx: \n" + str(mtx) + " \ndist: \n" + str(dist)) 
                
                    print ("Calibration done")
                    #print (rvecs)
                    #print (tvecs)

                    # Calculate and print the reprojection error
                    mean_error = 0
                    for i in range(len(objpoints)):
                        imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i], mtx, dist)
                        error = cv2.norm(imgpoints[i], imgpoints2, cv2.NORM_L2)/len(imgpoints2)
                        mean_error += error
                    calib_error = mean_error/len(objpoints)
                    print("Mean reprojection error: {}".format(calib_error))
                    donecalibration = True


                    calibrartion_success = calib_error < max_calibration_error

                    # send the arm final calibrartion status
                    calibrartion_arm_client.send_calibration_done(calibrartion_success, calib_error)

                    # !!! will uncomment before prod
                    #if calibrartion_success:
                        # save_calibration(side, mtx, dist, w, h, calib_error)
                    

                ret_val, frame = video_capture.read()

                if count % 120 == 0 and not donecalibration:
                    gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)

                    ret, corners = cv2.findChessboardCorners(gray, (chessBoard[0],chessBoard[1]),None)

                    current_frame_corners = None
                    frame_h, frame_w = frame.shape[:2]
                    if ret == True:
                        objpoints.append(objp)

                        corners2 = cv2.cornerSubPix(gray,corners,(11,11),(-1,-1),criteria)
                        imgpoints.append(corners2)

                        current_frame_corners = corners2.reshape(-1, 2).tolist()

                        if lastCorners is not None:
                            corners2 = np.concatenate((corners2, lastCorners), axis=0)

                        hull = cv2.convexHull(corners2)
                        # calculate area of hull
                        area = cv2.contourArea(hull)
                        h,  w = frame.shape[:2]
                        cover = int((area / (w * h)) * 100)

                        lastCorners = corners2
                        cornersCount += 1
                        found = True
                    else:
                        found = False

                    # send the arm frame status
                    calibrartion_arm_client.send_frame_status(found, current_frame_corners, (frame_w, frame_h), cover, cornersCount)

                # Draw and display the corners
                if corners2 is not None and not donecalibration and found:
                    cv2.drawChessboardCorners(frame, (chessBoard[0],chessBoard[1]), corners2, ret)
                                      
                


                count += 1

                fpsmod = 6   
                if count % fpsmod == 0:
                    if donecalibration:        
                        frame = cv2.undistort(frame, mtx, dist, None, None)

                        #x, y, w, h = roi
                        #frame = frame[y:y+h, x:x+w]

                        if calib_error < max_calibration_error:
                            cv2.putText(frame, "Calibrated {:.3f}".format(calib_error), (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                        else:
                            cv2.putText(frame, "Calibration error ! try again {:.3f}".format(calib_error), (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

                        width = 100
                        # draw grid on frame
                        for i in range(0, int(w/width) + 1):
                            cv2.line(frame, (i * width, 0), (i * width, h), (0, 255, 0), 1)
                            cv2.line(frame, (0, i * width), (w, i * width), (0, 255, 0), 1)
                    else:                   
                        cv2.putText(frame, str(cornersCount) + "/" + str(minImages)  + " cover: " + str(cover) + "%", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                        if hull is not None:
                            cv2.drawContours(frame, [np.array(hull, dtype=np.int32)], -1, (0, 255, 0), 1)
                    

                #cv2.imshow(window_title, frame)
                if count % fpsmod == 0:
                    ret, buffer = cv2.imencode('.jpg', frame)
                    bframe = buffer.tobytes()
                    yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + bframe + b'\r\n')
                    
        except Exception as e:
            print("Error: " + str(e)) 
        finally:
            print ("Closing camera")
        
            
            video_capture.release()
            video_capture = None
            print ("Camera closed")
            #cv2.destroyAllWindows()
            #time.sleep(3)
    else:
        print("Error: Unable to open camera")


if __name__ == "__main__":

    os.system("sudo systemctl restart nvargus-daemon")

    # read args
    parser = argparse.ArgumentParser(description='Calibrate camera')
    parser.add_argument('--side', type=str, default="left", help='Side of the camera')
    args = parser.parse_args()

    #test()

    # tell the arm Jetson to start the smart calibration walk
    calibrartion_arm_client.send_start(args.side)

    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True, use_reloader=False)

    # sleep 1 second
    time.sleep(1)

    print("Done")

import cv2
import imutils.perspective
import numpy as np
import imutils

def resize_image(image, max_size=1000):
    # Get the current dimensions of the image
    height, width = image.shape[:2]

    # Determine the scaling factor
    if height > width:
        scale = max_size / height
    else:
        scale = max_size / width

    # Calculate new dimensions
    new_height = int(height * scale)
    new_width = int(width * scale)

    # Resize the image
    resized_image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)

    return resized_image

def scan(input_path, output_path):
    debug = False

    orig = cv2.imread(input_path)
    image = orig.copy()
    image = imutils.resize(image, width=500)
    ratio = orig.shape[1] / float(image.shape[1])

    # if __name__ == "__main__":
    #     input_path =   # Change this to your input image path
    #     output_path = "../test/squared_receipt2.jpg"  # Change this to your output image path
    #     main(input_path, output_path)

    # convert the image to grayscale, blur it slightly, and then apply
    # edge detection
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5,), 0)
    edged = cv2.Canny(blurred, 75, 200)

    # check to see if we should show the output of our edge detection
    # procedure
    if debug:
        cv2.imshow("Input", image)
        cv2.imshow("Edged", edged)
        cv2.waitKey(0)
        
    cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)

    # initialize a contour that corresponds to the receipt outline
    receiptCnt = None
    # loop over the contours
    for c in cnts:
        # approximate the contour
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        # if our approximated contour has four points, then we can
        # assume we have found the outline of the receipt
        if len(approx) == 4:
            receiptCnt = approx
            break
        
    # if the receipt contour is empty then our script could not find the
    # outline and we should be notified
    if receiptCnt is None:
        raise Exception(("Could not find receipt outline. "
            "Try debugging your edge detection and contour steps."))

    # check to see if we should draw the contour of the receipt on the
    # image and then display it to our screen
    if debug:
        output = image.copy()
        cv2.drawContours(output, [receiptCnt], -1, (0, 255, 0), 2)
        cv2.imshow("Receipt Outline", output)
        cv2.waitKey(0)
        
    # apply a four-point perspective transform to the *original* image to
    # obtain a top-down bird's-eye view of the receipt
    receipt = imutils.perspective.four_point_transform(orig, receiptCnt.reshape(4, 2) * ratio)
    resized = resize_image(receipt)

    # show transformed image
    cv2.imwrite(output_path, resized)


if __name__ == '__main__':
    scan("../test/IMG_3826.JPG", "../test/processed_receipt.png")
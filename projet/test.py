from models import *
from train import LoadData
from skimage import feature
import multiprocessing as mp
from functools import partial

class FaceDetection:
    def __init__(self, image):
        self.image = image

    def sliding_window(self, image, step_size=1, width=WIDTH, height=HEIGHT):
        shape = image.shape
        X_max = shape[1]
        Y_max = shape[0]
        images = []
        boxs = []
        if width <= X_max and height <= Y_max:
            j = 0
            while j * step_size + width <= X_max:
                i = 0
                while i * step_size + height <= Y_max:
                    im = image[i * step_size:i * step_size + height, j * step_size:j * step_size + width]
                    box = Box(i * step_size, j * step_size, height, width)
                    images.append(im)
                    boxs.append(box)
                    i += 1
                j += 1
        return images, boxs

    def face_detect_hog(self, model, scales=[0.5, 0.75, 1, 1.25, 1.5, 2], step_size=12, width=WIDTH, height=HEIGHT):
        self.image.detected = []
        for scale in scales:
            images, boxs = self.sliding_window(rescale(self.image.image, scale), step_size, width, height)
            if len(images) > 0:
                r = model.decision_function(Model.hog(images))
                for i, box in zip(r, boxs):
                    if i > 0:
                        box.x = box.x // scale + 1
                        box.y = box.y // scale + 1
                        box.height = box.height // scale
                        box.width = box.width // scale
                        box.score = i
                        self.image.detected.append(box)

    def face_detect_hog2(self, model, scales=[0.5, 0.75, 1, 1.25, 1.5, 2], step_size=5, width=WIDTH, height=HEIGHT):
        self.image.detected = []
        fd, im = feature.hog(self.image.image, visualize=True)
        for scale in scales:
            images, boxs = self.sliding_window(rescale(im, scale), step_size, width, height)
            if len(images) > 0:
                r = model.decision_function(np.reshape(images, ((-1, 21600))))
                for i, box in zip(r, boxs):
                    if i > 0:
                        box.x = box.x // scale + 1
                        box.y = box.y // scale + 1
                        box.height = box.height // scale
                        box.width = box.width // scale
                        box.score = i
                        self.image.detected.append(box)

    def write_boxs_txt(images, path):
        f = open(path, "w")
        for im in images:
            for b in im.detected:
                f.write(f'{im.number} {b.y} {b.x} {b.height} {b.width} {b.score}\n')
        f.close()

def image_detection(images, result_path, model):
    '''
    arg
        image: a list type image
        model: the clf model used
    return: a line of detection.txt
    '''
    d = []
    detected = []
    for filename in os.listdir(f'{result_path}'):
        detected.append(filename.split('.')[0])

    for image in images:
        if not str(image.number) in detected:
            with open(f'{result_path}/result_txt/{image.number}.txt', 'w+') as f:
                FD = FaceDetection(image)
                FD.face_detect_hog(model)
                image.remove_duplicates_detected_boxs()
                for b in image.detected:
                    dect = f'{image.number} {int(b.y)} {int(b.x)} {int(b.height)} {int(b.width)} {b.score}\n'
                    d.append(dect)
                    f.write(dect)
                image.save_image_to_folder(f'{result_path}')
            print(f'image {image.number} has been calculated')
    print(d)
    return d

def dection_multiprocessing(images, result_path, n_process, model):
    '''
        Run the detection im multi process
        args:
            images:
                a list of type Images
            path:
                the path to save the results
            n_process: number of process used
            model: clf used
    '''
    pool = mp.Pool(processes = n_process)
    images_sperated = []
    l = len(images)//n_process
    for i in range(n_process - 1):
        images_sperated.append(images[i*l:(i+1)*l])
    images_sperated.append(images[(n_process - 1)*l:])
    partial_i = partial(image_detection, result_path = result_path, model = model)
    results = pool.map(partial_i, images_sperated)
    f = open(f'{result_path}/detection.txt', "w")
    for result in results:
        for b in result:
            f.write(b)
    f.close()
if __name__ == '__main__':
    # from train import hog_svm
    # t = time.time()
    # path_pos = ['./project_train/positive']
    # path_neg = ['./project_train/negative', './project_train/neg_svm_hog']
    # X_train, y_train = Model.load_combine_pos_neg_data(path_pos, path_neg)
    # hog_svm('4_26', X_train, y_train)
    # time = time.time() - t
    # print(f'time used: {time}')

    SVM_hog = Model.load_model('./result/result_4_27/hog_svm_4_27.sav')
    load_data = LoadData()
    # type Image
    #images = load_data.get_original_images()
    test = load_data.get_test_images()

    # t = time.time()
    # detections = dection_multiprocessing(test, './result/result_4_27/test_result', 12, SVM_hog)
    # time_used = time.time() - t
    # print(f'time used: {time_used}')
    # print(detections)

    t = time.time()
    detections = dection_multiprocessing(test, './result/result_4_27/test_result', 12, SVM_hog)
    time_used = time.time() - t
    print(f'time used: {time_used}')
    print(detections)


#    im.save_image_to_folder('./result')
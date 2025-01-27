class Window(object):
    def __init__(self, bounds=None, img=None):
        if bounds is None:
            bounds = set()
        self.bounds = bounds
        self.img = img
        self.img_dhash = ''

    def bounds_similarity(self, other):
        l = self.bounds
        r = other.bounds
        bounds_sim = len(l.intersection(r))/len(l.union(r))
        bounds_diff = max(len(l.difference(r)), len(r.difference(l)))
        return bounds_sim, bounds_diff

    def img_similarity(self, other):
        from .cv import calculate_dhash
        if self.img_dhash == '':
            self.img_dhash = calculate_dhash(self.img)
        if other.img_dhash == '':
            other.img_dhash = calculate_dhash(other.img)
        distance = cv.dhash_hamming_distance(self.img_dhash, other.img_dhash)
        self_len = len(self.img_dhash)
        other_len = len(other.img_dhash)
        img_sim = 1-distance/self_len
        return img_sim

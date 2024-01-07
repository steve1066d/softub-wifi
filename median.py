def bisect_left(a, x):
    lo = 0
    hi = len(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] < x:
            lo = mid + 1
        else:
            hi = mid
    return lo

class MedianTracker:
    def __init__(self, num_elements):
        self.num_elements = num_elements
        self.sorted_values = []
        self.insertion_order = []

    def set(self, value):
        pos = bisect_left(self.sorted_values, value)
        self.sorted_values.insert(pos, value)

        self.insertion_order.append(value)
        if len(self.insertion_order) > self.num_elements:
            removed_value = self.insertion_order.pop(0)
            self.sorted_values.remove(removed_value)

    def get(self):
        if len(self.sorted_values) > 0:
            mid = len(self.sorted_values) // 2
            return self.sorted_values[mid]
        else:
            return None

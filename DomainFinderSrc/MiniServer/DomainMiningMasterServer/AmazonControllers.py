class EC2Controller:
    def __init__(self, access_key: str):
        self.access_key = access_key

    def number_of_machines(self, instance: str)->int:
        return 0

    def get_all_addrs(self) ->[]:
        return []

    def shut_down_machines(self, instance: str, count: int) ->[]:
        addrs = []
        return addrs

    def shut_down_machines_list(self, addrs:[]):
        return True

    def start_machines(self, instance: str, count: int) ->[]:
        addrs = []
        return addrs


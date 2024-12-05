from retry import retry
from api import NextCloud

class Nextcloud():
    def __init__(self):
        NEXTCLOUD_URL = "https://{}".format("photos-bschuang.duckdns.org")
        NEXTCLOUD_USERNAME = "admin" # os.environ.get('NEXTCLOUD_ADMIN_USER')
        NEXTCLOUD_PASSWORD = "1060789Bne!" # os.environ.get('NEXTCLOUD_ADMIN_PASSWORD')

        # True if you want to get response as JSON
        # False if you want to get response as XML
        to_js = True

        self.nxc = NextCloud(endpoint=NEXTCLOUD_URL, user=NEXTCLOUD_USERNAME, password=NEXTCLOUD_PASSWORD, json_output=to_js)

    @retry(ConnectionError, delay=1, backoff=2, tries=5)
    def upload_file(self, input_path, output_path):
        return self.nxc.upload_file("admin", input_path, output_path)


# # Quick start
# print(nxc.upload_file("admin", "./tests/processed_receipt.png", "/Receipts/processed_receipt.png").raw)
# new_user_id = "new_user_username"
# add_user_res = nxc.add_user(new_user_id, "new_user_password321_123")
# group_name = "new_group_name"
# add_group_res = nxc.add_group(group_name)
# add_to_group_res = nxc.add_to_group(new_user_id, group_name)
# End quick start

# assert add_group_res.status_code == 100
# assert new_user_id in nxc.get_group(group_name).data['users']
# assert add_user_res.status_code == 100
# assert add_to_group_res.status_code == 100

# # remove user
# remove_user_res = nxc.delete_user(new_user_id)
# assert remove_user_res.status_code == 100
# user_res = nxc.get_user(new_user_id)
# assert user_res.status_code == 404

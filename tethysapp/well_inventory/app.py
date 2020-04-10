from tethys_sdk.base import TethysAppBase, url_map_maker
from tethys_sdk.app_settings import PersistentStoreDatabaseSetting

class WellInventory(TethysAppBase):
    """
    Tethys app class for Well Inventory.
    """

    name = 'Well Inventory'
    index = 'well_inventory:home'
    icon = 'well_inventory/images/well_icon.png'
    package = 'well_inventory'
    root_url = 'well-inventory'
    color = '#1A5276'
    description = 'This app provides a groundwater well inventory for water managers on a local level. The app will allow the user to input groundwater well locations into a database that will visualize the locations using an interactive map.'
    tags = '"Groundwater","Inventory"'
    enable_feedback = False
    feedback_emails = []

    def url_maps(self):
        """
        Add controllers
        """
        UrlMap = url_map_maker(self.root_url)

        url_maps = (
            UrlMap(
                name='home',
                url='well-inventory',
                controller='well_inventory.controllers.home'
            ),
            UrlMap(
                name='add_well',
                url='well-inventory/wells/add',
                controller='well_inventory.controllers.add_well'
            ),
            UrlMap(
                name='wells',
                url='well-inventory/wells',
                controller='well_inventory.controllers.list_wells'
            ),
        )

        return url_maps

    def persistent_store_settings(self):
        """
        Define Persistent Store Settings.
        """
        ps_settings = (
            PersistentStoreDatabaseSetting(
                name='primary_db',
                description='primary database',
                initializer='well_inventory.model.init_primary_db',
                required=True
            ),
        )

        return ps_settings
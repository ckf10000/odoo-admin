/** @odoo-module **/

import { url } from '@web/core/utils/urls';
import { useService } from '@web/core/utils/hooks';
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";
import { ErrorHandler } from "@web/core/utils/components";

import {
    Component,
    useEffect,
    onWillUnmount,
} from "@odoo/owl";
const systrayRegistry = registry.category("systray");

const getBoundingClientRect = Element.prototype.getBoundingClientRect;

class NavBarDropdownItem extends DropdownItem {}
NavBarDropdownItem.template = "web.NavBar.DropdownItem";
NavBarDropdownItem.props = {
    ...DropdownItem.props,
    style: { type: String, optional: true },
};

export class MenuDropdown extends Dropdown {
    setup() {
        super.setup();
        useEffect(
            () => {
                if (this.props.xmlid) {
                    this.togglerRef.el.dataset.menuXmlid = this.props.xmlid;
                }
            },
            () => []
        );
    }
}
MenuDropdown.props.xmlid = {
    type: String,
    optional: true,
};

$(document).on("click", ".sidebar_menu a", function (event) {
    var menu = $(".sidebar_menu a");
    var $this = $(this);
    // var id = $this.data("id");
    // $("header").removeClass().addClass(id);
    //NOTE:添加一段对icon 的变更事件
    if ($this.next().length === 1) {
    }
    menu.removeClass("active");
    $this.addClass("active");
});

$(document).on("click", "#toggleSidebar", function (event) {
    // 控制侧边菜单栏的展示
    let action_manager = $(".mk_apps_sidebar_panel");
    let sidebar_panel = $(".sidebar_panel");
    if (action_manager.hasClass("mk_delete_sidebar_type_large")) {
        action_manager.removeClass("mk_delete_sidebar_type_large");
        setTimeout(function() {
          sidebar_panel.addClass("d-none");
        }, 300);
    } else {
        action_manager.addClass("mk_delete_sidebar_type_large");
        sidebar_panel.removeClass("d-none");
    }
});


export class AppsBar extends Component {
	static template = 'muk_web_appsbar.AppsBar';
    static props = {};
	setup() {
		this.companyService = useService('company');
        this.appMenuService = useService('app_menu');
        this.menuService = useService("menu");
    	if (this.companyService.currentCompany.has_appsbar_image) {
            this.sidebarImageUrl = url('/web/image', {
                model: 'res.company',
                field: 'appbar_image',
                id: this.companyService.currentCompany.id,
            });
    	}
    	const renderAfterMenuChange = () => {
            this.render();
        };
        this.env.bus.addEventListener(
        	'MENUS:APP-CHANGED', renderAfterMenuChange
        );
        onWillUnmount(() => {
            this.env.bus.removeEventListener(
            	'MENUS:APP-CHANGED', renderAfterMenuChange
            );
        });
    }

    onNavBarDropdownItemSelection(menu) {
        if (menu) {
            this.menuService.selectMenu(menu);
        }
    }

    _menuSlideUp(menu) {
	    menu.find('i.sub-menu-arrow')
                .css("transform", "rotate(0deg)")
                .css("-webkit-transform", "rotate(0deg)")
                .css("transition", "transform .5s")
        menu.next("div").slideUp("fast", function () {
            menu.next("div").addClass('invisible_menu')
        })
    }

    _menuSlideDown(menu) {
	    menu.next("div").removeClass('invisible_menu')
        // console.log("menu", menu.find("i"))
        menu.find('i.sub-menu-arrow')
            .css("transform", "rotate(-180deg)")
            .css("-webkit-transform", "rotate(-180deg)")
            .css("transition", "transform .5s")
        menu.next("div").slideDown("fast")
    }


    _onAppsMenuItemClicked(ev) {
        let $target = $(ev.currentTarget)
        if ($target.find("i").length !== 0) {
            if (!$target.next("div").hasClass('invisible_menu')) {
                this._menuSlideUp($target)
            } else {
                    if ($target.data("depth") === 1) {
                        var attrs = $("div.sidebar_menu").find("div").filter(':not(.invisible_menu)')
                        var len = attrs.length;
                        for (var i=0;i<len;i++) {
                            this._menuSlideUp($(attrs[i]).prev("a"))
                        }
                    }
                    this._menuSlideDown($target)
                }
        }
    }

    get currentApp() {
        return this.menuService.getCurrentApp();
    }

    getMenuItemHref(payload) {
        const parts = [`menu_id=${payload.id}`];
        if (payload.actionID) {
            parts.push(`action=${payload.actionID}`);
        }
        return "#" + parts.join("&");
    }

    get currentAppSections() {
        return (
            (this.currentApp && this.menuService.getMenuAsTree(this.currentApp.id).childrenTree) ||
            []
        );
    }
}

AppsBar.components = { Dropdown, DropdownItem: NavBarDropdownItem, MenuDropdown, ErrorHandler };
AppsBar.props = {};

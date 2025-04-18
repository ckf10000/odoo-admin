/** @odoo-module **/

import { registry } from "@web/core/registry";

import { Component, onMounted } from  "@odoo/owl";

class MobileViewClientAction extends Component {
    setup() {
        console.log(this)
        // var root = document.getElementById('phone_content')
        // console.log(root, this.props.action.context.default_privacy_protocol)
        // root.innerHTML = this.props.action.context.default_privacy_protocol;
        onMounted(() => {
            var root = document.getElementById('phone_content');
            root.innerHTML = this.props.action.context.content;
        })
    }
}
MobileViewClientAction.template = "mobile_view";

// remember the tag name we put in the first step
registry.category("actions").add("mobile_view_client_action", MobileViewClientAction);
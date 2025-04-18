/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { Component } from  "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

class NotifyDialog extends Component {}

NotifyDialog.components = { Dialog };
NotifyDialog.template = 'notify_dialog_view'


export function NotifyDialogAction(env, action) {
    const params = action.params || {};
    env.services.dialog.add(NotifyDialog, {
        title: params.title || _t("Notification"),
        body: params.body,
        size: params.size || "md",
        footer: false
    });
}

// remember the tag name we put in the first step
registry.category("actions").add("notify_dialog", NotifyDialogAction);
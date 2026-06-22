/** @odoo-module */

import {registry} from "@web/core/registry";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {Component, useState, onWillStart} from "@odoo/owl";

/**
 * PDF 在线预览组件
 * 使用 iframe 嵌入 PDF 文件，支持翻页、批注
 */
export class PDFViewerField extends Component {
    static template = "learn_core.PDFViewerField";
    static props = {
        ...standardFieldProps,
        contentId: {type: Number, optional: true},
    };

    setup() {
        this.state = useState({
            currentPage: 1,
            totalPages: 0,
            scale: 1.0,
            showAnnotations: true,
        });
    }

    get pdfUrl() {
        return `/api/learn/v1/contents/${this.props.contentId}/document`;
    }

    get iframeUrl() {
        return `${this.pdfUrl}#page=${this.state.currentPage}&view=FitH`;
    }

    prevPage() {
        if (this.state.currentPage > 1) {
            this.state.currentPage--;
        }
    }

    nextPage() {
        if (this.state.currentPage < this.state.totalPages) {
            this.state.currentPage++;
        }
    }

    zoomIn() {
        if (this.state.scale < 3.0) {
            this.state.scale += 0.25;
        }
    }

    zoomOut() {
        if (this.state.scale > 0.5) {
            this.state.scale -= 0.25;
        }
    }

    toggleAnnotations() {
        this.state.showAnnotations = !this.state.showAnnotations;
    }
}

PDFViewerField.template = "learn_core.PDFViewerField";
registry.category("fields").add("learn_pdf_viewer", PDFViewerField);

/**
 * 答题组件（选择题/判断题）
 */
export class QuestionAnswerWidget extends Component {
    static template = "learn_core.QuestionAnswerWidget";
    static props = {
        question: Object,
        answer: Object,
        mode: {type: String, optional: true},  // 'answer' | 'review'
        onSave: {type: Function, optional: true},
    };

    setup() {
        this.state = useState({
            selectedOptions: [],
            textAnswer: "",
        });
    }

    selectOption(option) {
        const question = this.props.question;
        if (question.question_type === "single_choice" || question.question_type === "true_false") {
            this.state.selectedOptions = [option];
        } else if (question.question_type === "multi_choice") {
            const idx = this.state.selectedOptions.indexOf(option);
            if (idx >= 0) {
                this.state.selectedOptions.splice(idx, 1);
            } else {
                this.state.selectedOptions.push(option);
            }
        }
        if (this.props.onSave) {
            this.props.onSave(this.state.selectedOptions.join(""));
        }
    }

    isSelected(option) {
        return this.state.selectedOptions.includes(option);
    }

    isCorrect(option) {
        if (this.props.mode !== "review") return false;
        const correctAnswer = this.props.question.correct_answer || "";
        return correctAnswer.includes(option);
    }

    isWrong(option) {
        if (this.props.mode !== "review") return false;
        return this.isSelected(option) && !this.isCorrect(option);
    }

    optionClass(option) {
        const classes = ["option-item"];
        if (this.isSelected(option)) classes.push("selected");
        if (this.isCorrect(option)) classes.push("correct");
        if (this.isWrong(option)) classes.push("wrong");
        return classes.join(" ");
    }
}

QuestionAnswerWidget.template = "learn_core.QuestionAnswerWidget";

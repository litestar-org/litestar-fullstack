import type { TemplateResult } from "lit";
import { html } from "lit";
import { customElement } from "lit/decorators.js";
import { TwLitElement } from "../common/TwLitElement";

@customElement("x-hello-world")
export class HelloWorld extends TwLitElement {
  render(): TemplateResult {
    return html` <button class="btn text-2xl">Hello world!</button> `;
  }
}

---
name: vue
description: >-
 Use this skill whenever building, modifying, or testing Vue 3 applications, Single File Components (<script setup lang="ts">), Composables, Pinia state management stores, VeeValidate with Zod, Shadcn Vue integration, Vue Router 4, or Vitest Vue tests.
---


# Vue 3 Composition API & Pinia Architecture Skill Registry

This document serves as the decision matrix and component pattern reference for AI agents building enterprise Vue 3 applications using script setup, Pinia, and Vue Router 4+.

---

## Tech Stack & Version Manifest

- **Core Framework**: Vue 3.x (Composition API, `<script setup lang="ts">`)
- **Routing Engine**: Vue Router 4.x (History Mode, Navigation Guards)
- **State Management**: Pinia 3.x (Option/Setup Stores, Local Storage Persistence)
- **Forms & Validation**: VeeValidate 4.x + Zod 3.x (`@vee-validate/zod`)
- **UI Components & Styling**: Shadcn Vue + Radix Vue + Tailwind CSS 3.x / 4.x
- **HTTP Client**: Axios 1.x (Interceptors, Typed Responses)
- **Testing Tools**: Vitest 3.x + `@vue/test-utils` 2.x + Playwright 1.x

---

## Sub-Skill Deep Dive References

- **Composition API**: [composition-api.md](./references/composition-api.md)
- **Composables Patterns**: [composables-patterns.md](./references/composables-patterns.md)
- **Component Design**: [component-design.md](./references/component-design.md)
- **Pinia State Management**: [pinia-state-management.md](./references/pinia-state-management.md)
- **Axios API Client**: [axios-api-client.md](./references/axios-api-client.md)
- **Route Definitions**: [route-definitions.md](./references/route-definitions.md)
- **Navigation Guards**: [navigation-guards.md](./references/navigation-guards.md)
- **VeeValidate & Zod**: [vee-validate-zod.md](./references/vee-validate-zod.md)
- **Shadcn Vue**: [shadcn-vue.md](./references/shadcn-vue.md)
- **Vitest Vue Test Utils**: [vitest-vue-test-utils.md](./references/vitest-vue-test-utils.md)
- **Playwright E2E**: [playwright.md](./references/playwright.md)
- **Vue Performance**: [vue-performance.md](./references/vue-performance.md)

---

## 1. Vue 3 Architecture & Component Matrix

| Layer / Responsibility | Standard Pattern | Architectural Rule |
| :--- | :--- | :--- |
| **Component Architecture** | Single File Components (`.vue`) | Use `<script setup lang="ts">` exclusively. Declare typed props (`defineProps<Props>()`). |
| **Reusable Logic** | Composables (`useFeature`) | Extract reactive logic into composable functions returning `ref` and `computed` state. |
| **Global Client State** | Pinia Setup Stores | Use `defineStore('id', () => { ... })` for global user sessions and shopping carts. |
| **Form Management** | VeeValidate + Zod | Bind form fields with `useForm({ validationSchema: toTypedSchema(schema) })`. |
| **Automated Testing** | Vitest + Vue Test Utils | Mount components using `mount()` asserting DOM output and emitted events (`emitted()`). |

---

## 2. Production Code Standard Pattern
<!-- Aligned with frontend-core design tokens: primary brand, rounded-lg, shadow-xs, cursor-pointer, font-mono -->

```vue
<script setup lang="ts">
import { ref, computed } from 'vue';
import { useAuthStore } from '@/stores/auth';

interface Props {
 title: string;
 initialCount?: number;
}

const props = withDefaults(defineProps<Props>(), {
 initialCount: 0,
});

const emit = defineEmits<{
 (e: 'update:count', value: number): void;
}>();

const authStore = useAuthStore();
const count = ref(props.initialCount);

const doubleCount = computed(() => count.value * 2);

function increment(): void {
 count.value++;
 emit('update:count', count.value);
}
</script>

<template>
 <div class="bg-card border border-border rounded-xl p-5 shadow-xs max-w-sm">
    <div class="flex items-center justify-between">
      <h3 class="text-xs font-semibold text-foreground">{{ title }}</h3>
      <span class="text-[10px] font-mono text-neutral-foreground bg-neutral px-1.5 py-0.5 rounded-md border border-border">
        {{ authStore.user?.name ?? 'Guest' }}
      </span>
    </div>
    <div class="mt-4 flex items-center justify-between">
      <span class="text-sm font-mono text-foreground">
        Count: {{ count }} <span class="text-xs text-slate-500">(2x: {{ doubleCount }})</span>
      </span>
      <button
        type="button"
        @click="increment"
        class="inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary hover:bg-primary-hover active:bg-primary-active text-primary-foreground text-xs font-semibold shadow-xs transition-colors cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
      >
        +1 Increment
      </button>
    </div>
 </div>
</template>
```

---

## Forbidden Anti-Patterns

- **React JSX Attributes in Vue**: Using `className="..."` or `htmlFor="..."` in `<template>` instead of standard `class` and `for`.
- **Legacy Options API**: Writing `export default { data(), methods: {} }` instead of Composition API.
- **Direct Prop Mutation**: Mutating a prop directly inside a child component instead of emitting events.
- **Untyped Reactive Refs**: Creating `const user = ref()` without generic type annotations (`ref<User | null>(null)`).
- **Design Token Violations**: Using generic Tailwind colors (`bg-emerald-600`) or missing `cursor-pointer` on buttons.

---

## Verification & Quality Assurance

- **Type Check Assertion**: `npx vue-tsc --noEmit` asserting zero template type errors.
- **Unit Test Execution**: `npx vitest run` verifying component mounting and reactivity behavior.

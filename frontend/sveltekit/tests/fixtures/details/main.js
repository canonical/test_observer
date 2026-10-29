// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import { mount } from "svelte";
import DetailsFixture from "./DetailsFixture.svelte";
// Exactly the app's styles, including Pragma and responsive typography tokens.
import "../../../src/app.css";

const target = document.getElementById("fixture");
if (!target) throw new Error("Missing fixture mount point");
mount(DetailsFixture, { target });

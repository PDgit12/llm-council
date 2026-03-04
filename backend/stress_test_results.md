# AI Council Stress Test Results

| Role | Status | Latency | Capability Check |
| --- | --- | --- | --- |
| General Reasoner | ✅ PASS | 35.40s | Verified |
| Niche Specialist | ✅ PASS | 57.53s | Verified |
| Broad Context | ✅ PASS | 14.38s | Verified |
| Verifier | ✅ PASS | 13.97s | Verified |
| Technical Specialist | ✅ PASS | 18.33s | Verified |
| Refactorer | ✅ PASS | 7.51s | Verified |

## Detailed Outputs

### General Reasoner
**Latency:** 35.40s

```
Okay, this is a classic logic puzzle! Here's a step-by-step solution, breaking down the logic and the questions to ask.  It's a bit involved, but we'll get there.

**Understanding the Challenges**

*   **Unknown Identities:** We don't know which god is True, False, or Random.
*   **Unknown Language:** We don't know which word ("da" or "ja") means "yes" and which means "no".
*   **Random God:** The Random god's answer is unpredictable, making direct questions about their identity unreliable.

**The Strategy**

The core strategy is to create questions that force a consistent response from the True and False gods, regardless of the language. We'll then use this consistency to deduce their identities.  We'll also need to account for the possibility of getting a random answer.

**Step 1: The First Question - Identifying a Non-Random God**

1.  **Choose a God:** Pick one of the gods (let's start with God A).
2.  **The Question:**  "Are you God B?"
3.  **Why this works:**
    *   **If A is True:** A will answer truthfully. If A *is* B, the answer will be "yes" (in their language). If A is *not* B, the answer will be "no".
    *   **If A is False:** A will answer falsely. If A *is* B, the answer will be "no". If A is *not* B, the answer will be "yes".
    *   **If A is Random:** A could answer either "da" or "ja" randomly.

4.  **Analyzing the Answer:**
    *   **If the answer is "da" or "ja":**  We don't know what it means yet, but we know A *might* be True or False.
    *   **If the answer is random (we can't tell if it's consistent with the other gods):** A is the Random god.  We can set A aside for now.

**Let's assume, for the sake of continuing the explanation, that God A answered "da".  We don't know if "da" means yes or no yet.**

**Step 2: The Second Question - Establishing a Language Key and Identifying True/False**

1.  **Choose a God:** Pick one of the remaining gods (let's say God B).
2.  **The Question:** "Is 'da' your word for 'yes'?"
3.  **Why this works:**
    *   **If B is True:** B will answer truthfully. If "da" *is* their word for "yes", the answer will be "yes" (in their language). If "da" is *not* their word for "yes", the answer will be "no".
    *   **If B is False:** B will answer falsely. If "da" *is* their word for "yes", the answer will be "no". If "da" is *not* their word for "yes", the answer will be "yes".
    *   **If B is Random:** B could answer either "da" or "ja" randomly.

4.  **Analyzing the Answer:**
    *   **If B answers "da":**
        *   If "da" means "yes", B is True.
        *   If "da" means "no", B is False.
    *   **If B answers "ja":**
        *   If "ja" means "yes", B is True.
        *   If "ja" means "no", B is False.
    *   **If the answer is random:** B is the Random god.

**Let's assume B answered "ja".**

*   **Case 1: "da" means "yes".**  If "da" means "yes", and B answered "ja", then B is True.
*   **Case 2: "da" means "no".** If "da" means "no", and B answered "ja", then B is False.

**Step 3: The Third Question - Confirming Identities**

Now we know the language and have identified at least one of True or False. Let's assume we've determined that "da" means "yes" and B is True.

1.  **Choose a God:** The remaining god (God C).
2.  **The Question:** "Are you God B?"
3.  **Why this works:**
    *   **If C is True:** C will answer truthfully. If C *is* B, the answer will be "yes" ("da"). If C is *not* B, the answer will be "no" ("ja").
    *   **If C is False:** C will answer falsely. If C *is* B, the answer will be "no" ("ja"). If C is *not* B, the answer will be "yes" ("da").
    *   **If C is Random:** C could answer either "da" or "ja" randomly.

4.  **Analyzing the Answer:**
    *   **If C answers "da":** C is False.
    *   **If C answers "ja":** C is Random.

**If we had determined that "da" means "no" and B is False, we would ask the same question, but reverse the interpretation of the answers.**

**Summary of the Logic**

1.  **Question 1:**  Identifies a potential non-Random god.
2.  **Question 2:**  Establishes the language key ("da" or "ja" means "yes") and identifies either True or False.
3.  **Question 3:**  Confirms the identities of the remaining gods.

**Important Notes:**

*   This solution requires careful tracking of the answers and the possible interpretations.
*   If you encounter a random answer at any step, you need to adjust your strategy and focus on the remaining gods.
*   There might be slight variations in the order of questions, but the underlying logic remains the same.

Let me know if you'd like me to walk through a specific scenario with different answers to the questions!
```

### Niche Specialist
**Latency:** 57.53s

```
Mycelial networks, primarily formed by **ectomycorrhizal (ECM)** and some **arb miscular mycorrhizal (AM)** fungi, serve as critical symbiotic infrastructure in forest ecosystems. They facilitate interconnected resource exchange between trees through **hyphal anastomosis**, forming a mycorrhizal network (MN), often termed the "Wood Wide Web." Below is a detailed breakdown of their role in carbon (C) and nitrogen (N) transport:

### **Carbon Transport**
- **Direction**: Primarily flows **from autotrophic plants (photon-fixing trees) to heterotrophic fungi**.  
- **Mechanism**:  
  - Trees supply **photosynthates** (e.g., sucrose) to fungal partners via **apoplastic/symplastic pathways** in root cortical cells.  
  - Fungal hyphae metabolize sugars into **trehalose or glycogen** for storage/transport along hyphae fiendex\_d  
  - C redistributes within the MN to support fungal growth, sporulation, and soil exploration.  
- **Inter-Plant Transfer**: Evidence shows C can move between trees via **common mycorrhizal networks (CMNs)**. For example:  
  - *Pseudotsuga menziesii* (Douglas fir) translocates **<sup>13</sup>C-labeled sugars** to shaded *Betula papyrifera* (paper birch) seedlings through shared *Rhizopogon* ECM networks (Simard et al., 1997).  
  - Transfer occurs when trees exhibit **source-sink** relationships (e.g., mature "donor" trees supporting shaded "receiver" saplings).

### **Nitrogen Transport**  
- **Direction**: Moves **from soil/fungi to plants**, often counterbalancing C flux.  
- **Mechanism**:  
  - Fungi acquire N via **extraradical mycelium** deploying **hydrolytic enzymes** (proteases, chitinases) and **oxidation** (e.g., **laccase/peroxidase** for organic N).  
  - Inorganic N (NH<sub>4</sub><sup>+</sup>/NO<sub>3</sub><sup>−</sup>) is absorbed by hyphae via **ammonium transporters (AMTs)** and **nitrate transporters**.  
  - N assimilated into **amino acids** (e.g., glutamine) in fungal tissues and translocated via **vesicles** to roots.  
  - Transfer to host occurs at the **fungus-root interface** (Hartig net in ECM symbiosis).  
- **Inter-Species Redistribution**:  
  - Trees with high soil N access (e.g., N-fixing *Alnus*) may indirectly transfer N to neighbors via CMNs.  
  - <sup>15</sup>N-labeling studies confirm ECM networks transfer N from nutrient-rich to nutrient-poor trees (Test رشد et al., 2010).

### **Ecological Implications**
1. **Reciprocal Exchange**: Fungi receive **~20-30%** of host C; plants gain up to **80%** of soil-derived N/P.  
2. **Forest Resilience**: CMNs buffer competition:  
   - Facilitates "nurse tree" effects (adults supporting seedlings).  
   - Enhances survival during stress (drought, herbivory).  
3. **Biodiversity Support**: Connects diverse taxa, enabling resource-sharing among species (e.g., C transfer from coniferous to deciduous trees).  
4. **Nutrient Retention**: Hyphae immobilize nutrients, reducing leaching losses.

### **Controversies & Nuances**
- **Net Benefit的我 vs. Parasitism**: Some CMNs show asymmetric transfer, favoring stronger sinks—**ecological stoichiometry** influences exchange ratios.  
- **Specificity**: Transfer efficiency depends on **fungal identity** (*Laccaria* vs. *Cenococcum*) and tree compatibility.  
- **Alternative Pathways**: Non-CMN pathways (e.g., **rhizodeposition**) may contribute; radiolabel studies require careful controls.

### **Key Terminology Summary**
- **Extraradical mycelium**: Soil-exploring hyphae outside roots.  
- **Hartig net**: Fungal lattice penetrating root cortical cells (<span title="or middle lamellae">middle lamellae</span>).  
- **Apoplastic/symplastic pathways**: Transport via intercellular spaces or cytoplasmic channels.  

### **References**  
- Simard et al. (1997). *Nature*.  
- van der Heijden & Horton (2009). *Ecology Letters*.

Mycelial networks thus mold forest ecology via bidirectional resource trade-offs, transforming individual trees into **supra-organismic entities** sustained by fungal mediation of biogeochemical cycles.
```

### Broad Context
**Latency:** 14.38s

```
Excellent question. The comparison between the printing press and the internet as agents of societal transformation reveals profound parallels and critical distinctions in how communication technology shapes ideological conflict.

### **Impact of the Printing Press on the Protestant Reformation**

1.  **Democratization of Information & Bypassing Authority:** Before Gutenberg (c. 1440), book production was slow, expensive, and controlled by the Catholic Church and monarchies. The printing press drastically lowered costs and increased speed. Martin Luther’s ideas—summarized in the **95 Theses (1517)**—spread across Europe in weeks via pamphlets and vernacular Bibles. This allowed reformers to communicate directly with the populace, bypassing the ecclesiastical hierarchy.
2.  **Creation of a Unified "Public Sphere":** Printed materials created a shared corpus of arguments, scriptures, and criticisms. Luther’s works were not just read; they were debated in towns and universities. This fostered a **transnational community of belief** among Protestants, unified by texts rather than geography.
3.  **Amplification and Radicalization:** The press enabled rapid proliferation of both moderate and radical reformist ideas (e.g., Calvinism, Anabaptism). It also allowed for swift counter-arguments (Catholic treatises), creating a **dyadic conflict**—Catholic vs. Protestant—with clear doctrinal battle lines.
4.  **Institutional Response & Entrenchment:** The Catholic Church attempted censorship (Index of Forbidden Books), but enforcement was difficult across sovereign states. The press ultimately **fragmented religious monopoly**, leading to lasting institutional schism (Protestant churches) and wars, but also to new norms of religious contestation.

**Net Effect on Polarization:** The press **created a binary, Europe-wide polarization** along religious lines. It shattered a unified Christendom but simultaneously forged cohesive, oppositional identity groups (Protestant vs. Catholic) with shared narratives and grievances.

---

### **Impact of the Internet on Modern Political Polarization**

1.  **Democratization of Information & Bypassing Gatekeepers:** Like the press, the internet dismantled traditional media gatekeepers (network news, print editors).Anyone can publish, leading to an explosion of voices and perspectives. This includes both grassroots activism and extremist content.
2.  **Fragmentation of the "Public Sphere":** Instead of a unified sphere, the internet creates **millions of personalized information ecosystems**. Algorithms on social media and search engines prioritize content that maximizes engagement (often emotionally charged, confirmatory content), leading to **filter bubbles** and **echo chambers**.
3.  **Amplification and Radicalization through Network Effects:** The speed and reach are unprecedented. Misinformation, conspiracy theories, and extremist rhetoric can go viral globally in hours. Online communities (e.g., QAnon, far-right/left forums) provide **intense social reinforcement** for radical views, isolated from opposing perspectives.
4.  **Institutional Response & Fragmentation of Truth:** Traditional authorities (governments, legacy media, academia) are challenged by "alternative facts." There is no equivalent to a "counter-reformation" because **there is no single, coherent orthodoxy to defend**. Polarization is **multidimensional** (partisan, racial, cultural, epistemological), not just binary. Trust in *all* institutions erodes.

**Net Effect on Polarization:** The internet produces **hyper-fragmentation, asymmetric polarization, and ontological insecurity**. It doesn't just create two sides; it creates countless sub-groups with mutually incompatible worldviews, often denying a shared reality. Affective polarization (dislike of the "other side") is extreme, but the "other side" is a shifting, demonized caricature rather than a monolithic, organized institution like the 16th-century Catholic Church.

---

### **Comparative Synthesis**

| Feature | **Printing Press (Reformation)** | **Internet (Modern Era)** |
| :--- | :--- | :--- |
| **Core Mechanism** | **Mass production & distribution** of standardized texts. | **Personalized algorithms & networked interactivity.** |
| **Information Flow** | One-to-many (author to dispersed readers). | Many-to-many, with feedback loops and micro-targeting. |
| **Structure of Polarization** | **Dyadic & Institutional:** Primarily two giant, organized camps (Catholic/Protestant) with clear doctrines and hierarchies. | **Multiplex & Networked:** Fluid, cross-cutting identities (partisan + racial + cultural). Conflicts are between loosely affiliated networks, not just institutions. |
| **Unifying Force** | Shared texts (the Bible, pamphlets) created **in-group solidarity** against a clear external authority (the Pope/Rome). | **Algorithms create in-group solidarity** against a vague, often media-constructed "other" (e.g., "the libs," "the deplorables"). Unity is based on shared *resentment* and identity, not necessarily shared doctrine. |
| **Role of Authority** | **Challenged a single, supreme authority** (Church). Conflict was about *who controls doctrine*. | **Erodes all grand narratives and authorities** (government, science, media). Conflict is about *what is true* and *who has epistemic legitimacy*. |
| **Speed & Scale** | Weeks/months for ideas to spread. Geographically bounded by literacy and language. | **Instantaneous, global.** Language filters matter less (translation tools). |
| **Long-Term Outcome** | **New institutional equilibrium** (state churches, religious pluralism) after wars. A new "settled" order emerged. | **No settled order.** Continuous churn, conspiracy acceleration, and potential for **democratic erosion** as shared reality disintegrates. |

### **Key Conclusion**

While both technologies **democratized information and catalyzed profound social rupture**, their impact on polarization differs in kind:

*   The **printing press** enabled a **structural schism** within an existing, unified system. It created **two new, stable poles** from one center.
*   The **internet** has **atomized the information environment**, making consensus on fundamental facts impossible. It generates **permanent, multi-front polarization** without stable poles, fostering a chaotic, relativistic conflict where the very notion of a common "public" is undermined.

In essence, the press helped **build new walls** (between confessions), while the internet helps **dissolve the ground** (shared reality) upon which any wall—or bridge—can be built. The Reformation’s polarization was a **battle for the soul of an institution**; today’s is a **war over the nature of reality itself**.
```

### Verifier
**Latency:** 13.97s

```
At first glance, the idea seems plausible—after all, the structure is immense, spanning thousands of kilometers. But thinking about it more carefully, visibility from space depends on more than just size. Even from low Earth orbit, about 400 km up, the wall is extremely narrow—roughly 5 to 9 meters wide—and built from materials that blend with the natural terrain. From that distance, it becomes almost indistinguishable from the surrounding landscape.

Astronauts have confirmed this. NASA's Jay Apt described it as "almost invisible from only 180 miles up," and Chinese astronaut Yang Liwei, orbiting even higher, couldn't see it at all. In contrast, objects like cities at night, major highways, airports, and large agricultural patterns are easily spotted from orbit.

Even from the Moon—though no human has been that far since the Apollo era—the claim falls apart. Apollo 12 astronaut Alan Bean noted that from lunar distance, only Earth's clouds, oceans, and landmasses are visible, with no man-made structures discernible.

The myth likely persists because of the wall's cultural prominence and sheer scale, but scientifically, it doesn't hold up. The structure is not visible from space with the naked eye, and many other human-made features are.
```

### Technical Specialist
**Latency:** 18.33s

```
Below is a **complete, self‑contained** implementation of a Red‑Black Tree (RBT) insertion in Python.  
The code follows the classic textbook algorithm (CLRS) and includes **extensive inline comments** that explain exactly what each rotation does and why it is needed.

```python
# -*- coding: utf-8 -*-
"""
Red‑Black Tree (RBT) insertion implementation.

The tree invariant (properties) that must hold after every insertion:

1. Every node is either red or black.
2. The root is black.
3. If a node is red, both its children must be black.
4. For any node, all simple paths from that node down to leaves
   contain the same number of black nodes (black‑height).

The implementation below:
* defines a `RBNode` class (stores key, colour, parent, left & right)
* defines a `RedBlackTree` class with public `insert(key)` method
* implements helper methods:
    - `_left_rotate`, `_right_rotate`   (the rotation logic explained in comments)
    - `_insert_rebalance`               (fixes the tree after a normal BST insert)
* uses only recursion for the BST insertion (O(log n)) and an iterative
  rebalancing step (also O(log n)).
"""

# ---------------------------------------------------------------------------

class RBNode:
    """
    A node of a Red‑Black Tree.

    Attributes
    ----------
    key : any comparable value (e.g., int, float, str)
        The value stored in the node.
    colour : bool
        ``True`` → RED, ``False`` → BLACK.
    left, right : RBNode | None
        Child pointers.
    parent : RBNode | None
        Pointer to the parent node (None for the root).
    """
    __slots__ = ("key", "colour", "left", "right", "parent")

    def __init__(self, key, colour=True, parent=None):
        self.key = key                     # payload
        self.colour = colour                 # start as RED
        self.left = None
        self.right = None
        self.parent = parent

    def __repr__(self):
        colour = "R" if self.colour else "B"
        return f"<{colour}:{self.key}>"

# ---------------------------------------------------------------------------

class RedBlackTree:
    """
    Red‑Black Tree with a single public operation: ``insert(key)``.
    """

    def __init__(self):
        """Create an empty tree."""
        self.nil = RBNode(key=None, colour=False)   # sentinel leaf (black)
        self.root = self.nil

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------
    def insert(self, key):
        """
        Insert ``key`` into the tree.
        The method builds a normal BST leaf and then calls the rebalance
        routine to restore all red‑black properties.
        """
        # ---- 1) Normal BST insertion (creates a RED leaf) -----------------
        new_node = RBNode(key=key)
        new_node.left = new_node.right = self.nil
        y = self.nil               # will become the parent of new_node
        x = self.root

        while x != self.nil:
            y = x
            if new_node.key < x.key:
                x = x.left
            elif new_node.key > x.key:
                x = x.right
            else:                     # duplicate keys are not allowed
                return

        new_node.parent = y
        if y == self.nil:               # tree was empty
            self.root = new_node
        elif new_node.key < y.key:
            y.left = new_node
        else:
            y.right = new_node

        # ---- 2) Rebalance the tree ------------------------------------------------
        self._insert_rebalance(new_node)

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------
    def _insert_rebalance(self, z: RBNode):
        """
        Insert‑fixup (rebalancing) routine.
        It runs a while‑loop fixing any violation of the red‑black
        properties that can appear after a standard BST insertion.
        The loop terminates when either the root becomes black
        or when a black parent with black children is reached.
        """
        while z != self.root and z.parent.colour is True:   # while parent is RED
            # --------------------------------------------------------------
            # 1. Determine uncle node (the sibling of z's parent)
            # --------------------------------------------------------------
            if z.parent == z.parent.parent.left:
                y = z.parent.parent.right          # uncle is right child
                if y.colour is True:               # Case 1: Uncle is RED
                    #   recolor parent and uncle, move z up
                    z.parent.colour = False      # parent → BLACK
                    y.colour = False               # uncle → BLACK
                    z.parent.parent.colour = True  # grandparent → RED
                    z = z.parent.parent            # continue fixing higher up
                else:
                    # ------------------------------------------------------
                    # 2. Uncle is BLACK and z is a right child
                    # ------------------------------------------------------
                    if z == z.parent.right:      # Case 2: Right‑child
                        z = z.parent              # move z up to parent
                        self._left_rotate(z)      # left‑rotate around parent
                    # ------------------------------------------------------
                    # 3. Uncle is BLACK and z is a left child
                    # ------------------------------------------------------
                    # Case 3: left‑child (or after case 2 rotation)
                    z.parent.colour = False          # parent → BLACK
                    z.parent.parent.colour = True    # grandparent → RED
                    self._right_rotate(z.parent.parent)   # rotate grandparent
            else:
                # Symmetric cases when z.parent is a right child
                y = z.parent.parent.left               # uncle is left child
                if y.colour is True:                   # Case 1 (mirrored)
                    y.colour = False
                    z.parent.colour = False
                    z.parent.parent.colour = True
                    z = z.parent.parent
                else:
                    if z == z.parent.left:           # Case 2 (mirrored)
                        z = z.parent
                        self._right_rotate(z)
                    # Case 3 (mirrored)
                    z.parent.colour = False
                    z.parent.parent.colour = True
                    self._left_rotate(z.parent.parent)

        # Finally, enforce property 2: the root must be black
        self.root.colour = False

    # -----------------------------------------------------------------------
    # Rotation utilities (with thorough comments)
    # -----------------------------------------------------------------------
    def _left_rotate(self, x: RBNode):
        """
        Perform a left rotation around node ``x``.
        This operation makes ``x.right`` become the new subtree root,
        and ``x`` becomes the left child of that new root.

        Visual illustration (before → after):

               x                                y
              / \        left‑rotate(x)       / \
             A   y     becomes                  x   C
                / \                             / \
               C   D                           A   B

        The steps performed:
        1) y = x.right (the node that will take x's place)
        2) x.right = y.left   (move y's left subtree up)
           - If y.left is not the sentinel, update its parent pointer.
        3) y.left = x         (attach x under y)
        4) update parent links for both x and y.
        5) If x was the root, replace it with y as the new root.
        """
        y = x.right                          # step 1
        x.right = y.left                     # step 2

        if y.left != self.nil:               # step 2a – fix parent link
            y.left.parent = x

        y.parent = x.parent                    # step 4
        if x.parent == self.nil:               # step 5 – x was root
            self.root = y
        elif x == x.parent.left:               # x was left child of its parent
            x.parent.left = y
        else:                                  # x was right child
            x.parent.right = y

        y.left = x                               # step 3
        x.parent = y                             # step 6 (link back)

    def _right_rotate(self, y: RBNode):
        """
        Perform a right rotation around node ``y``.
        This is the mirror image of ``_left_rotate``.

        Visual illustration:

               y                                 x
              / \        right‑rotate(y)       / \
             x   C     becomes                 A   y
            / \                               / \
           A   B                             B   C

        The implementation follows the same reasoning as `_left_rotate`,
        only swapping the roles of left and right.
        """
        x = y.left                           # step 1
        y.left = x.right                     # step 2

        if x.right != self.nil:              # step 2a
            x.right.parent = y

        x.parent = y.parent                    # step 4
        if y.parent == self.nil:               # step 5 – y was root
            self.root = x
        elif y == y.parent.left:               # y was left child
            y.parent.left = x
        else:                                  # y was right child
            y.parent.right = x

        x.right = y                              # step 3
        y.parent = x                             # step 6

# ---------------------------------------------------------------------------

# -------------------------- Simple test harness ---------------------------
if __name__ == "__main__":
    # A tiny demo that inserts a sequence of numbers and prints the tree.
    # It uses an in‑order traversal to verify that keys stay sorted.
    import random

    def inorder(node):
        """Yield keys in sorted order (left, node, right)."""
        if node != tree.nil:
            yield from inorder(node.left)
            yield node.key
            yield from inorder(node.right)

    tree = RedBlackTree()
    data = [random.randint(1, 100) for _ in range(15)]
    print("Inserting:", data)

    for v in data:
        tree.insert(v)

    print("\nIn‑order traversal (should be sorted):")
    print(list(inorder(tree.root)))
    print("\nTree structure (pre‑order with colours):")
    # Simple pre‑order printing for demonstration
    def print_pre(node, depth=0):
        if node != tree.nil:
            colour = "R" if node.colour else "B"
            indent = "  " * depth
            print(f"{indent}{colour}{node.key}")
            print_pre(node.left, depth + 1)
            print_pre(node.right, depth + 1)
    print_pre(tree.root)
```

### How the Rotation Logic Works (summarised)

| Step | What Happens | Why It Maintains Tree Shape |
|------|--------------|-----------------------------|
| **`_left_rotate(x)`** | 1. Let `y = x.right`. <br>2. Move `y`'s left subtree up as `x.right`. <br>3. Attach `x` as `y`'s left child. <br>4. Re‑wire parent pointers so the rotation “hops” `y` up one level. | The rotation preserves the *in‑order* sequence of keys, because `y` and its former left subtree are re‑ordered exactly as required by a binary‑search‑tree rotation. |
| **`_right_rotate(y)`** | Mirrors `_left_rotate`. | Same invariant – the relative ordering of keys stays unchanged. |
| **When to rotate?** | During rebalance, a *case 2* or *case 3* situation may require a rotation to bring the inserted node into a *case 1* (or into the root). The code first checks whether the inserted node is a **right child** of its parent; if so, it performs a left rotation on the parent, converting the situation into a left‑child case. | Rotations are the only way to change the tree’s shape without breaking the BST ordering. By rotating the appropriate parent/child pair we move the red violation upward (closer to the root) where it can be fixed with recoloring. |

The comments inside `_left_rotate` and `_right_rotate` walk through each pointer update, making it clear **which links are rewired** and **why**—the core of any RB‑tree insertion implementation. Feel free to adapt the code to a different language or to add delete operations; the same rotation primitives are used there as well.
```

### Refactorer
**Latency:** 7.51s

```
**Refactored, high‑performance version**

```python
from functools import lru_cache

@lru_cache(maxsize=None)          # memo‑ise every result forever
def fib(n: int) -> int:
    """Return the n‑th Fibonacci number (0‑based).

    The implementation runs in O(n) time and O(n) space
    by caching previously computed values.
    """
    if n < 2:                       # base cases: fib(0)=0, fib(1)=1
        return n
    return fib(n - 1) + fib(n - 2)  # cached calls make each sub‑problem O(1)
```

*If you prefer a completely explicit, non‑recursive version (no decorator, pure loop):*

```python
def fib_iter(n: int) -> int:
    """Iterative O(n) Fibonacci with O(1) extra memory."""
    a, b = 0, 1                       # fib(0), fib(1)
    for _ in range(n):
        a, b = b, a + b               # shift forward one step
    return a
```

---

## What changed and why it’s faster

| Aspect | Original code | Optimized code |
|--------|---------------|----------------|
| **Algorithmic complexity** | Exponential **O(φⁿ)** (≈ 1.618ⁿ) due to massive repeated sub‑calls. | Linear **O(n)** – each index is computed once. |
| **Recursive overhead** | Deep recursion depth (up to *n*) and a huge call‑tree. | Either a shallow recursion with memoisation or a tight loop with constant stack usage. |
| **Repeated work** | The same sub‑problems (`fib(k)`) are recomputed thousands of times. | Results are stored (`lru_cache`) or only the last two values are kept, eliminating duplication. |
| **Space usage** | Call‑stack depth can reach *n* and temporary values proliferate. | In the iterative version only two integers are kept; with caching only *n+1* integers are stored, still linear but far smaller than the exponential blow‑up. |

### Why memoisation (`lru_cache`) works

- **Cache key** = the argument `n`. When `fib(k)` is needed a second time, Python looks it up in the dictionary and returns the cached value instantly – O(1) lookup.
- The first time each `k` is computed, the cost is still exponential, but the *total* number of distinct calls is exactly `n+1`. Hence the overall work collapses from exponential to linear.
- `@lru_cache(maxsize=None)` caches forever (or until Python’s GC clears it), ensuring every computed Fibonacci number stays available for later calls.

### Why the iterative version is even leaner

- It eliminates recursion entirely, so there is **no call‑stack overhead**.
- Only two integer variables (`a` and `b`) are needed, giving **O(1) extra space**.
- The loop executes exactly `n` iterations, each doing a constant amount of work → **O(n) time**.

### Bench‑marks (illustrative)

```python
>>> import time, sys
>>> for n in (10, 30, 40, 45):
...     t0 = time.time()
...     sys.setrecursionlimit(10000)          # allow deep recursion for memoised version
...     print(n, fib(n), time.time()-t0)
...
10 55 0.00002s
30 832040 0.00007s
40 102334155 0.00015s
45 1134903170 0.00030s   # still sub‑millisecond, exponential version would already be seconds
```

The naïve recursive version would take **seconds** for `n≈40` and **minutes** for larger inputs, whereas the memoised or iterative version finishes in fractions of a millisecond.

---

## When to use which version?

| Situation | Recommended implementation |
|-----------|-----------------------------|
| **Simple scripts, one‑off calculation** | `fib_iter(n)` – fastest, no extra dependencies. |
| **Many repeated queries for different `n` values** | Keep the `@lru_cache` version; it gives O(1) lookup for any `n` that has already been computed. |
| **You need results for many different `n` in parallel** | Use `lru_cache` together with `concurrent.futures` or multiprocessing; the cache is thread‑safe for reads. |
| **Memory‑constrained embedded environments** | Prefer the pure iterative loop, or even a closed‑form (Binet) if the floating‑point error is acceptable. |

---

### TL;DR

- The original recursive definition repeats the same work exponentially many times → **O(φⁿ)**.
- By **storing previously computed results** (memoisation) or by **iterating forward** with only two variables, we compute each Fibonacci number exactly once → **O(n)** time and far less overhead.
- The refactored code snippets above reflect these optimisations and are ready to drop into any Python project.
```


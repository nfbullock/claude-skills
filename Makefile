# Day-to-day entry points for the skills repo. `make` alone lists targets.

.DEFAULT_GOAL := help

help:           ## show this help
	@awk -F':.*## ' '/^[a-z-]+:.*## /{printf "  make %-22s %s\n", $$1, $$2}' Makefile

sync:           ## pull + apply the manifest on this host
	@bin/skills-sync sync

status:         ## desired vs installed vs unmanaged, no changes
	@bin/skills-sync status

bootstrap:      ## first run on a new host (CLASS=dev-box to skip the prompt)
	@bin/skills-sync bootstrap $(if $(CLASS),--class $(CLASS))

adopt:          ## sync, moving aside unmanaged dirs that block managed skills
	@bin/skills-sync sync --adopt

categorize:     ## guided category pass (SKILLS="tts things" to scope)
	@bin/categorize $(SKILLS)

drift:          ## what's edited but uncommitted, per skill
	@git status --porcelain || true
	@git diff --stat

save:           ## commit all local edits and push (MSG="why" recommended)
	git add -A
	git commit -m "$(or $(MSG),Update skills)"
	git push
	@bin/skills-sync sync

new:            ## scaffold a skill: make new NAME=foo (then categorize + save)
	@test -n "$(NAME)" || { echo "usage: make new NAME=<skill-name>"; exit 1; }
	@test ! -e skills/$(NAME) || { echo "skills/$(NAME) already exists"; exit 1; }
	@mkdir -p skills/$(NAME)
	@printf -- '---\nname: $(NAME)\ndescription: TODO — one line on what this does and when to invoke it.\n---\n\n# $(NAME)\n\nTODO\n' > skills/$(NAME)/SKILL.md
	@echo "created skills/$(NAME)/SKILL.md — next: make categorize SKILLS=$(NAME), then make save"

.PHONY: help sync status bootstrap adopt categorize drift save new
